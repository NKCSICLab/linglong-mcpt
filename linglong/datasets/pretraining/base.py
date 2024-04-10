import json
import pathlib
import warnings
import dataclasses

import linglong


class FileLoader:

    def __init__(
            self,
            file_list: list[pathlib.Path],
            special_tokens: dict[str, str],
            tokenizer: linglong.Tokenizer,
    ):
        self.file_list = file_list
        self.special_tokens = special_tokens
        self.tokenizer = tokenizer
        self.progbar = linglong.tqdm(total=len(file_list))
        self.current_file_idx = 0
        self.text_pool = []

    def empty(self) -> bool:
        return self.current_file_idx >= len(self.file_list)

    def load(self, length: int, stride: int) -> list[str]:
        while len(self.text_pool) < length + 1 and self.current_file_idx < len(self.file_list):
            with open(self.file_list[self.current_file_idx], 'r') as f:
                self.current_file_idx += 1
                self.progbar.update(1)
                self.text_pool.append(self.special_tokens['start_token'])
                for line in f:
                    self.text_pool.extend(self.tokenizer.tokenize(line))
                self.text_pool.append(self.special_tokens['end_token'])
        input_tokens = self.text_pool[:length]
        self.text_pool = self.text_pool[stride:]
        return input_tokens


@dataclasses.dataclass
class PreTrainingDatasetConfig:
    input_path: str | pathlib.Path
    output_path: str | pathlib.Path
    vocab_path: str
    special_tokens: dict[str, str]
    stride: int
    items_per_file: int
    n_position: int
    use_pinyin: bool = False
    pinyin_vocab_path: str | None = None
    use_cache: bool = False
    extra_config: dict | None = None

    def __post_init__(self):
        self.input_path = pathlib.Path(self.input_path)
        self.output_path = pathlib.Path(self.output_path) / f'template-0{"-pinyin" if self.use_pinyin else ""}'


class PreTrainingDataset:

    def __init__(self, config: PreTrainingDatasetConfig):
        self.config = config
        self.input_file_list = self.config.input_path.rglob('*.txt')
        self.tokenizer, self.pinyin_tokenizer = linglong.get_tokenizers(
            vocab_path=self.config.vocab_path,
            pinyin_vocab_path=self.config.pinyin_vocab_path,
            special_tokens=self.config.special_tokens,
            use_pinyin=self.config.use_pinyin,
        )
        self.file_format = None

        self.config.output_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _discard_obj(obj, discarded: list, reason: str | None = None):
        warnings.warn(f'{linglong.prettify(obj)} is discarded. Reason: {reason}')
        warnings.warn(f'{len(discarded)} items are discarded.')
        discarded.append(obj)

    def _process(self) -> tuple[dict, list]:
        file_loader = FileLoader(
            list(self.input_file_list),
            special_tokens=self.config.special_tokens,
            tokenizer=self.tokenizer,
        )
        discarded = []
        writer = None
        file_idx = None
        meta = {
            'padding_shape': self.config.n_position,
            'count': 0,
            'files': [],
            'compression_type': 'GZIP',
            'has_attention_mask': False,
            'has_labels': False,
        }
        item_id = 0
        import linglong.data.tfrecord
        import tensorflow as tf
        while not file_loader.empty():
            input_tokens = file_loader.load(length=self.config.n_position, stride=self.config.stride)
            input_ids = self.tokenizer.convert_tokens_to_ids(input_tokens)
            pinyin_input_ids = None
            if self.config.use_pinyin:
                pinyin_input_ids = self.pinyin_tokenizer.convert_tokens_to_ids(input_tokens)
                if len(input_ids) != len(pinyin_input_ids):
                    self._discard_obj(
                        input_tokens,
                        discarded,
                        reason=f'`input_ids` and `pinyin_input_ids` have different lengths: '
                               f'{len(input_ids)} vs {len(pinyin_input_ids)}. '
                               f'(most likely due to omitted control characters.)',
                    )
                    continue
            new_file_idx = item_id // self.config.items_per_file
            if new_file_idx != file_idx:
                if writer is not None:
                    writer.close()
                file_idx = new_file_idx
                filename = f'{file_idx + 1:08d}.tfrecord.gz'
                meta['files'].append(filename)
                writer = tf.io.TFRecordWriter(str(self.config.output_path / filename), options='GZIP')
            writer.write(linglong.data.tfrecord.serialize_example(
                data=input_ids,
                pinyin=pinyin_input_ids,
            ))
            meta['count'] += 1
            item_id += 1
        if writer is not None:
            writer.close()
        return meta, discarded

    def prepare(self) -> tuple[str, str]:
        meta_path = self.config.output_path / 'train-meta.json'
        if not (self.config.use_cache and meta_path.is_file()):
            meta, discarded = self._process()
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)
            if len(discarded) > 0:
                print(f'\n{len(discarded)} items are discarded.')
        return str(meta_path.absolute()), str(self.config.output_path.absolute())
