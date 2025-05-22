# UUID Generator

A robust, production-ready UUID generator written in Python. This utility supports UUID v1 (time-based), UUID v4 (random), and timestamp-based UUIDs with optional prefix and categorization. It persists all generated UUIDs in an SQLite database and includes duplicate detection, metadata storage, logging, and stats reporting.

## 📌 Features

* Supports UUID v1, v4, and custom timestamp-based UUIDs.
* Optional prefix and category for enhanced classification.
* Persists UUIDs in a SQLite database.
* Advanced logging with file rotation.
* Built-in statistics for generated UUIDs by type and category.
* Duplicate detection and custom exception handling.


## 🚀 Usage

Run the generator using the command line:

```bash
python uuid_generator.py --type <v1|v4|timestamp> [--category CATEGORY] [--prefix PREFIX] [--stats]
```

### Examples

Generate a v1 UUID with a category:

```bash
python uuid_generator.py --type v1 --category "session"
```

Generate a timestamp-based UUID with a prefix:

```bash
python uuid_generator.py --type timestamp --prefix ABC --category "order"
```

View usage statistics:

```bash
python uuid_generator.py --stats
```

## 📈 Output

Example UUID output:

```
Generated UUID: 550e8400-e29b-41d4-a716-446655440000
```

Statistics example:

```json
{
  "by_type": {
    "v1": 10,
    "v4": 8,
    "timestamp": 5
  },
  "by_category": {
    "session": 10,
    "order": 5
  },
  "total": 23
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This project is intended for demonstration, prototyping, or internal tooling purposes. While it includes best practices such as input validation, logging, and exception handling, it is not guaranteed to be secure or suitable for all production use cases without review and testing.

This software is provided "as is" without warranty of any kind, express or implied. The authors are not responsible for any legal implications of generated license files or repository management actions.  **This is a personal project intended for educational purposes. The developer makes no guarantees about the reliability or security of this software. Use at your own risk.**
