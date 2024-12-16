#!/usr/bin/env python3

import argparse
import configparser
import logging
# import os
import shutil
import signal
import subprocess
import sys
# import time
from dataclasses import dataclass
from multiprocessing.pool import Pool
from pathlib import Path
from threading import Timer
from typing import List, Optional

from generator_new import CSourceGenerator


@dataclass
class AnalyzerConfig:
    """Configuration for pointer analysis tools"""
    compiler_path: str
    tools: List[str]
    csmith_runtime: str
    timeout: int
    blacklist: List[str]


class PointerAnalyzerTester:
    """Differential testing framework for pointer analyses"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.source_generator = CSourceGenerator()

    def _load_config(self, config_path: Optional[str]) -> AnalyzerConfig:
        """Load configuration from file or use defaults"""
        default_tools = [
            '/home/work/SVF/build_asan/bin/wpa -lander --print-pts -stat=false',
            '/home/work/SVF/build_asan/bin/wpa -wander --print-pts -stat=false',
            '/home/work/SVF/build_asan/bin/wpa -hlander --print-pts -stat=false',
        ]

        if not config_path:
            return AnalyzerConfig(
                compiler_path='/home/work/llvm10/llvm/build_debug/bin/clang',
                tools=default_tools,
                csmith_runtime='/home/work/csmith/runtime',
                timeout=3600,
                blacklist=self._load_blacklist()
            )

        config = configparser.ConfigParser()
        config.read(config_path)
        return AnalyzerConfig(
            compiler_path=config['DIFFPTS']['Compiler'],
            tools=config['DIFFPTS'].get('Tools', default_tools),
            csmith_runtime=config['DIFFPTS']['CSmithRuntime'],
            timeout=config['DIFFPTS'].getint('Timeout', 3600),
            blacklist=self._load_blacklist()
        )

    def _load_blacklist(self) -> List[str]:
        """Load blacklist patterns from file"""
        try:
            with open('black_list', 'r') as f:
                return [line.strip() for line in f]
        except FileNotFoundError:
            return []

    def _generate_bitcode(self, c_file: Path) -> Optional[Path]:
        """Generate LLVM bitcode from C file"""
        bc_file = c_file.with_suffix('.bc')
        cmd = [
            self.config.compiler_path,
            f'-I{self.config.csmith_runtime}',
            '-emit-llvm', '-g', '-c',
            str(c_file), '-o', str(bc_file)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=35, text=True)
            if result.returncode != 0:
                logging.error(f"Compilation failed: {result.stderr}")
                return None
            return bc_file
        except subprocess.TimeoutExpired:
            logging.error("Compilation timed out")
            return None
        except Exception as e:
            logging.error(f"Compilation error: {e}")
            return None

    def _run_analyzer(self, tool_cmd: str, bitcode: Path) -> Optional[str]:
        """Run a single analyzer on the bitcode"""
        cmd = tool_cmd.split() + [str(bitcode)]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            is_timeout = [False]
            timer = Timer(
                self.config.timeout,
                lambda p, t: p.terminate() or t.__setitem__(0, True),
                args=[process, is_timeout]
            )
            timer.start()

            output = process.communicate()[0]
            timer.cancel()

            if is_timeout[0]:
                logging.warning(f"Analysis timed out for {tool_cmd}")
                return None

            return output

        except Exception as e:
            logging.error(f"Analysis error: {e}")
            return None

    def _check_output_for_errors(self, output: str) -> bool:
        """Check if analyzer output contains errors"""
        error_patterns = ['Assertion', 'Sanitizer', 'PrintStackTrace', 'Segment']

        if any(pattern in output for pattern in error_patterns):
            if not any(pattern in output for pattern in self.config.blacklist):
                return True
        return False

    def analyze_bitcode(self, bitcode: Path, output_dir: Path) -> None:
        """Run all analyzers on a bitcode file and check for inconsistencies"""
        results = []

        for tool in self.config.tools:
            output = self._run_analyzer(tool, bitcode)
            if output is None:
                continue

            if self._check_output_for_errors(output):
                logging.info(f"Found error in {bitcode}")
                shutil.copy(bitcode, output_dir / "crash" / bitcode.name)
            else:
                results.append(output)

        if len(results) >= 2 and not all(r == results[0] for r in results):
            logging.info(f"Found inconsistency in {bitcode}")
            shutil.copy(bitcode, output_dir / "crash" / bitcode.name)

    def generate_and_test(self, worker_id: int, output_dir: Path, count: int) -> None:
        """Generate programs and test analyzers"""
        input_dir = output_dir / "input"
        counter = 0

        while counter < count:
            c_file = input_dir / f"input_{worker_id}_{counter}.c"

            if self.source_generator.generate_source(str(c_file), check_ub=True):
                if bc_file := self._generate_bitcode(c_file):
                    self.analyze_bitcode(bc_file, output_dir)
                    bc_file.unlink()

            c_file.unlink(missing_ok=True)
            counter += 1


def main():
    parser = argparse.ArgumentParser(description="Differential Testing for Pointer Analyses")
    parser.add_argument('--output', default='/tmp/analysis-results', type=Path)
    parser.add_argument('--count', default=1000, type=int)
    parser.add_argument('--workers', default=1, type=int)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--seed-dir', type=Path)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    output_dir = args.output
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True)
    (output_dir / "crash").mkdir()
    (output_dir / "input").mkdir()

    tester = PointerAnalyzerTester(args.config)
    pool = Pool(args.workers)

    def signal_handler(sig, frame):
        pool.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        if args.seed_dir:
            bitcodes = list(args.seed_dir.glob('**/*.bc'))
            chunks = [bitcodes[i::args.workers] for i in range(args.workers)]

            for chunk in chunks:
                pool.apply_async(
                    lambda files: [tester.analyze_bitcode(f, output_dir) for f in files],
                    (chunk,)
                )
        else:
            for i in range(args.workers):
                pool.apply_async(
                    tester.generate_and_test,
                    (i, output_dir, args.count)
                )

        pool.close()
        pool.join()

    except KeyboardInterrupt:
        pool.terminate()
        sys.exit(0)


if __name__ == "__main__":
    main()
