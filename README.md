# FuzzIt: A Comprehensive Fuzzing Framework

FuzzIt is a sophisticated fuzzing framework designed for program analysis and testing, with a particular focus on pointer analysis (PTA) and call graph (CG) analysis. This library provides tools for generating test cases, performing differential testing, and analyzing results.

## Repository Structure

The repository is organized into several key components:

### Core Library (`fuzzlib/`)

The core library provides reusable components for fuzzing operations:

- **Generators**: Utilities for program generation
  - `program_generation.py`: Core program generation functionality
  - `parsing_utils.py`: Tools for parsing code and analysis results
  - `optimization_utils.py`: Optimization-related utilities
  - `sanitizer_utils.py`: Integration with sanitizer tools

- **Mutators**: Implements various mutation strategies
  - EMI (Equivalence Modulo Inputs) mutations
  - Attribute mutations
  - Options-based mutations

- **Reducer**: Implements test case reduction techniques

- **Tests**: Contains test cases for the library components

### Specialized Fuzzing Components

#### Pointer Analysis Fuzzing (`fuzz-pta/`)

Implements differential testing for pointer analysis:
- `generator.py`/`generator_new.py`: Program generation for PTA testing
- `pts_diff.py`/`pts_diff_new.py`: Differential analysis implementation
- `setup_env.py`: Environment setup utilities
- `config.py`: Configuration settings
- `black_list`: Blacklisting mechanism for specific test cases

#### Call Graph Analysis Fuzzing (`fuzz-cg/`)

Focuses on call graph analysis fuzzing:
- `main.py`: Main implementation
- `log_analyzer.py`: Analysis of fuzzing logs
- `stats.py`: Statistics gathering and reporting
- `config.py`: Configuration settings
- `ptaconfig.example.jsonc`: Example configuration

### Support Tools

- **`bin_tools/`**: Contains binary utilities for the fuzzing process
- **`com.sh`**: Shell script for common operations

## Technical Stack

The project leverages several key technologies:

- **Python Core** with dependencies:
  - `z3-solver` (4.13.0): For constraint solving and formal verification
  - `tqdm` (~4.67): For progress tracking in long-running operations
  - `jsmin` (3.0.1): For processing JavaScript/JSON configuration files

- **External Tools Integration**:
  - Compiler toolchains (GCC, Clang)
  - Program generators (YARPGen, CSmith)
  - Custom parsing tools

## Getting Started

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/fuzzit.git
   cd fuzzit
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the tool paths in the respective configuration files:
   - `fuzz-pta/config.py`
   - `fuzz-cg/config.py`

### Usage

#### Pointer Analysis Fuzzing

```bash
cd fuzz-pta
python pts_diff.py --config your_config.json --workers 4 --count 1000
```

#### Call Graph Analysis Fuzzing

```bash
cd fuzz-cg
python main.py --config your_config.jsonc
```

## Advanced Features

1. **Differential Testing**: Compare results from different analysis implementations to find discrepancies
2. **Program Generation**: Generate test programs using built-in generators or external tools
3. **Resource Management**: Memory limiting, timeout handling, and parallel processing
4. **Analysis and Reporting**: Log analysis and statistics gathering
5. **Sanitizer Integration**: Support for sanitizer-based testing
6. **Seed Management**: Support for seed-based fuzzing for reproducibility

## Related Projects

- [ECFuzz](https://github.com/ecfuzz/ECFuzz): A related fuzzing project

## License

[Your License Information]

## Contributors

[Your Contributor Information]