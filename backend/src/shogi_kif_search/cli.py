# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""CLIとしてのエントリーポイントを提供するモジュール。"""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from shogi_kif_search.game import iter_positions
from shogi_kif_search.kif import read_kif

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """KIFファイルの全局面の手数・SFEN・ハッシュをTSVで出力する。

    Args:
        argv: コマンドライン引数のリスト。

    Returns:
        処理の結果。
    """
    parser = argparse.ArgumentParser(
        description="KIFファイルから全局面のSFENとZobristハッシュを出力する。",
    )
    parser.add_argument(
        "kif_path",
        type=Path,
        help="読み込むKIFファイルのパス",
    )
    args = parser.parse_args(argv)

    try:
        game = read_kif(args.kif_path)

        lines = ["move\tsfen\thash"]
        lines.extend(
            f"{record.move_number}\t{record.sfen}\t0x{record.hash_value:016x}"
            for record in iter_positions(game)
        )

    # UnicodeDecodeError は ValueError の一種なので先に処理
    except UnicodeDecodeError:
        sys.stderr.write(f"{args.kif_path}: 文字コードを読めません。UTF-8 と cp932 に対応しています。\n")
        return 1
    except (OSError, ValueError) as error:
        sys.stderr.write(f"{args.kif_path}: {error}\n")
        return 1

    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
