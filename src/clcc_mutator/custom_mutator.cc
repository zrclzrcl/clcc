#include <cassert>
#include <fstream>
#include <iostream>
#include <memory>
#include <stack>
#include <string>
#include <stdio.h>
#include "afl-fuzz.h"
#include "config_validate.h"
#include "db.h"
#include "env.h"
#include "yaml-cpp/yaml.h"

struct ZrclMutator {
	ZrclMutator() : fuzz_now(0),fuzz_next(1) {
		strcpy(LLM_in_dir, "/home/LLM_testcase/");
	}
	~ZrclMutator() {

	}
  bool zrcl_is_have_new_in();
	char LLM_in_dir[50];
	int fuzz_now;
	int fuzz_next;
};

struct SquirrelMutator {
  SquirrelMutator(DataBase *db) : database(db),select(false) {}
  ~SquirrelMutator() { delete database; }
  DataBase *database;
  std::string current_input;
  ZrclMutator zrcl_mutator;
  bool select;
};

bool ZrclMutator::zrcl_is_have_new_in() {
    char LLM_in_path[100] = {0};
    char file_name[50] = {0};

    snprintf(file_name, sizeof(file_name), "LLM_G_%d.txt", fuzz_next);
    snprintf(LLM_in_path, sizeof(LLM_in_path), "%s%s", LLM_in_dir, file_name);

    if (access(LLM_in_path, F_OK) == 0) {
        return true;
    } else {
        return false;
    }
}


extern "C" {

void *afl_custom_init(afl_state_t *afl, unsigned int seed) {
  const char *config_file_path = getenv(kConfigEnv);
  if (!config_file_path) {
    std::cerr << "You should set the enviroment variable " << kConfigEnv
              << " to the path of your config file." << std::endl;
    exit(-1);
  }
  std::string config_file(config_file_path);
  std::cerr << "Config file: " << config_file << std::endl;
  YAML::Node config = YAML::LoadFile(config_file);
  if (!utils::validate_db_config(config)) {
    std::cerr << "Invalid config!" << std::endl;
  }
  auto *mutator = create_database(config);
  return new SquirrelMutator(mutator);
}

void afl_custom_deinit(SquirrelMutator *data) { delete data; }

u8 afl_custom_queue_new_entry(SquirrelMutator *mutator,
                              const unsigned char *filename_new_queue,
                              const unsigned char *filename_orig_queue) {
  // read a file by file name
  std::ifstream ifs((const char *)filename_new_queue);
  std::string content((std::istreambuf_iterator<char>(ifs)),
                      (std::istreambuf_iterator<char>()));
  mutator->database->save_interesting_query(content);
  return false;
}

unsigned int afl_custom_fuzz_count(SquirrelMutator *mutator,
                                   const unsigned char *buf, size_t buf_size) {

  mutator->select = !(mutator->zrcl_mutator.zrcl_is_have_new_in());
  if(mutator->select)
  {
    std::string sql((const char *)buf, buf_size);
    return mutator->database->mutate(sql);
  }
  return 1;
}

size_t afl_custom_fuzz(SquirrelMutator *mutator, uint8_t *buf, size_t buf_size,
                       u8 **out_buf, uint8_t *add_buf,
                       size_t add_buf_size,  // add_buf can be NULL
                       size_t max_size) {
  if (mutator->select)
  {
    DataBase *db = mutator->database;
    assert(db->has_mutated_test_cases());
    mutator->current_input = db->get_next_mutated_query();
    *out_buf = (u8 *)mutator->current_input.c_str();
    return mutator->current_input.size();
  }
  else
  {
    char LLM_in_path[100] = {0};
    char file_name[50] = {0};

    snprintf(file_name, sizeof(file_name), "LLM_G_%d.txt", mutator->zrcl_mutator.fuzz_next);  
    snprintf(LLM_in_path, sizeof(LLM_in_path), "%s%s", mutator->zrcl_mutator.LLM_in_dir, file_name);

		FILE* file = fopen(LLM_in_path, "r");

		if (file == NULL) {
			return 0;
		}

		fseek(file, 0, SEEK_END);
		size_t file_size = ftell(file);
		rewind(file);

		*out_buf = (unsigned char*)malloc(file_size);
		size_t bytes_read = fread(*out_buf, 1, file_size, file);

		fclose(file);
    mutator->zrcl_mutator.fuzz_next++;
    mutator->zrcl_mutator.fuzz_now++;
		return bytes_read;
  }
  
}
}
