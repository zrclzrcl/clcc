# Third-Party Notices

This file lists third-party software that may be used, built, or redistributed with CLCC, along with their respective licenses and attribution notices.

The licenses and notices below apply to the referenced third-party projects, not to CLCC itself.  
For CLCC’s license, see the repository `LICENSE` file.

> Tip: If you redistribute CLCC as a source/binary release or Docker image that includes third-party code/binaries, you should also include the corresponding third-party license texts (and NOTICE files if provided by upstream).

---

## 1) Squirrel

**Project**: Squirrel (coverage-guided DBMS fuzzer)  
**Repository**: https://github.com/s3team/Squirrel  
**License**: MIT License (see upstream `LICENSE`)

Squirrel is a grammar-aware DBMS fuzzing framework. CLCC is developed based on/with inspiration from Squirrel.

---

## 2) AFL++

**Project**: AFL++ (American Fuzzy Lop plus plus)  
**Repository**: https://github.com/AFLplusplus/AFLplusplus  
**License**: Apache License 2.0 (see upstream `LICENSE`)

AFL++ is a fuzzing framework used by many fuzzing projects. Squirrel (and therefore CLCC’s workflow/tooling) may rely on AFL++ components.

---

## 3) SQLRight

**Project**: SQLRight (A General Platform to Test DBMS Logical Bugs)  
**Repository**: https://github.com/PSU-Security-Universe/sqlright  
**License**: MIT License (see upstream `LICENSE`)

SQLRight combines the coverage-based guidance, validity-oriented mutations and oracles to detect logical bugs for DBMS systems.

---

## 4) DBMS Targets (Built/Downloaded in Docker)

CLCC supports fuzzing multiple DBMS engines. Depending on your setup, these DBMSs may be built or downloaded during Docker image build/run. Their licenses are governed by the upstream DBMS projects.

### SQLite
**Website**: https://sqlite.org/  
**License**: Public Domain

### PostgreSQL
**Website**: https://www.postgresql.org/  
**License**: The PostgreSQL License

### MySQL Community Server
**Website**: https://www.mysql.com/  
**License**: GPLv2 (Community Edition)

### MariaDB Server
**Website**: https://mariadb.org/  
**License**: GPLv2 (Community Server)

### DuckDB
**Website**: https://duckdb.org/  
**License**: MIT License

---

## 5) Where to find full license texts

Whenever possible, prefer including upstream license files verbatim in your distribution (e.g., under `third_party/<name>/LICENSE`).  
If you do not vendor third-party source code in this repository, you can refer to upstream license files:

- Squirrel MIT license: https://github.com/s3team/Squirrel/blob/main/LICENSE  
- SQLRight MIT license: https://github.com/PSU-Security-Universe/sqlright/blob/main/LICENSE
- AFL++ Apache-2.0 license: https://github.com/AFLplusplus/AFLplusplus/blob/stable/LICENSE  
- Apache License 2.0 text: https://www.apache.org/licenses/LICENSE-2.0  
- SQLite public domain statement: https://sqlite.org/copyright.html  
- PostgreSQL license page: https://www.postgresql.org/about/licence/  
- DuckDB MIT license: https://github.com/duckdb/duckdb/blob/main/LICENSE  
- MariaDB licensing FAQ: https://mariadb.com/docs/general-resources/community/community/faq/licensing-questions/licensing-faq  
- MySQL GPL licensing (Oracle doc): https://downloads.mysql.com/docs/licenses/mysqld-8.0-gpl-en.pdf
