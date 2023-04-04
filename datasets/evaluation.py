import fire
import numpy as np

from typing import *

import mcpt
import mcpt.evaluation


def main(
        dataset: str,
        input_path: str,
        cache_path: str,
        dataset_config: str,
        vocab: str = '../common/vocab/char-13312.txt',
        pinyin_vocab: str = '../common/vocab/pinyin-1354.txt',
        use_pinyin: bool = False,
        use_cache: bool = False,
        special_tokens: Optional[Dict[str, str]] = None,
        slicer: Optional[str] = '0:3',
):
    with mcpt.running('Loading configs') as spinner:
        special_tokens = {
            'start-token': '[MASK]',
            'end-token': '[CLS]',
            'part-separator': '[unused1]',
            'segment-separator': '[unused2]',
            **(special_tokens or {}),
        }
        config = mcpt.merge_configs({
            'dataset': dataset,
            'dataset-config': dataset_config,
            'input-path': input_path,
            'cache-path': cache_path,
            'vocab': vocab,
            'pinyin-vocab': pinyin_vocab,
            'use-pinyin': use_pinyin,
            'use-cache': use_cache,
            'special-tokens': special_tokens,
        }, mcpt.load_config(dataset_config, key=dataset))
        tokenizer = mcpt.Tokenizer(vocab)
        spinner.write(mcpt.print_dict(config, export=True))

    with mcpt.running(f'Loading {dataset} dataset', spinner=use_cache):
        x, y_true, candidates = mcpt.evaluation.load_dataset(config)
        if slicer is not None:
            slicer = slice(*(int(x) for x in slicer.split(':')))
            x, y_true = x[slicer], y_true[slicer]

    print(mcpt.text('Examples:', style=mcpt.INFO))
    output: Dict[str, Any] = {
        'example_count': len(x),
        'examples': [],
    }
    for i in range(len(x)):
        example = {}
        if isinstance(x[i], np.ndarray):
            x[i] = [x[i]]
        x_ids = [str(_.tolist()) for _ in x[i]]
        x_str = [tokenizer.convert_ids_to_string(list(_[0][0] if use_pinyin else _[0])) for _ in x[i]]
        example['x'] = x_ids if len(x_ids) > 1 else x_ids[0]
        example['x_str'] = x_str if len(x_str) > 1 else x_str[0]
        if y_true[i] is not None:
            if isinstance(y_true[i], np.ndarray):
                y_true[i] = [y_true[i]]
            y_true_ids = [str(_.tolist()) for _ in y_true[i]]
            example['y_true'] = y_true_ids if len(y_true_ids) > 1 else y_true_ids[0]
            if not config.get('use-perplexity', False):
                y_true_str = [tokenizer.convert_ids_to_string(list(_)) for _ in y_true[i]]
                example['y_true_str'] = y_true_str if len(y_true_str) > 1 else y_true_str[0]
        else:
            example['y_true'] = None
        output['examples'].append(example)
    output['candidates'] = candidates
    mcpt.print_dict(output)


if __name__ == '__main__':
    mcpt.init()
    fire.Fire(main)
