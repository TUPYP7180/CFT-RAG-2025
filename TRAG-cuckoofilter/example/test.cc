#include "cuckoofilter.h"

#include <assert.h>
#include <math.h>

#include <iostream>
#include <vector>
#include <string>
#include <stdio.h>
#include <map>
#include <utility>
#include <queue>
#include <set>
#include <unordered_map>

using cuckoofilter::CuckooFilter;
using cuckoofilter::EntityTree;
using cuckoofilter::EntityNode;
using cuckoofilter::EntityInfo;
using cuckoofilter::EntityAddr;
using cuckoofilter::EntityStruct;

namespace cuckoofilter {
    std::unordered_map<std::string, EntityInfo*> addr_map;
    EntityInfo * temp_info;
    EntityInfo * result_info;
    std::set<uint64_t> first_hash;
}

std::string trim(const std::string& str) {
    size_t first = str.find_first_not_of(" \t\n\r\f\v"); 
    if (first == std::string::npos) return ""; 
    size_t last = str.find_last_not_of(" \t\n\r\f\v"); 
    return str.substr(first, (last - first + 1)); 
}

std::vector<std::string> split(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::istringstream stream(str);
    std::string token;

    while (std::getline(stream, token, delimiter)) {
        tokens.push_back(trim(token)); 
    }

    return tokens;
}

int main(int argc, char **argv) {

  std::cout << "at the beginning, bucket_count of map_addr: " << cuckoofilter::addr_map.bucket_count() << std::endl;

  std::cout << "char: " << sizeof(char) << std::endl;
  std::cout << "EntityInfo *: " << sizeof(EntityInfo*) << std::endl;

  FILE * in = fopen("entities_file.csv", "r");
  char input[1024];
  std::set<std::pair<std::string, std::string>> data;
  std::set<std::string> out_degree;
  std::set<std::string> root_list;
  std::set<std::string> entity_set;

  while (fgets(input, 1020, in) != NULL){
    std::vector<std::string> result = split(input, ',');
    if (result.size() == 2){
      data.insert({result[0], result[1]});
      out_degree.insert(result[0]);
      entity_set.insert(result[0]), entity_set.insert(result[1]);

      EntityStruct s0 = {result[0]}, s1 = {result[1]};
      cuckoofilter::first_hash.insert(uint64_t(s0));
      cuckoofilter::first_hash.insert(uint64_t(s1));

    }
  }
  fclose(in);

  for (std::pair<std::string, std::string> edge : data){
    if (!out_degree.count(edge.second)) root_list.insert(edge.second);
  }

  std::cout << "total number of entities: " << entity_set.size() << std::endl; // 3148
  std::cout << "total number of first_hash: " << cuckoofilter::first_hash.size() << std::endl; // 3148
  std::cout << "total number of roots: " << root_list.size() << std::endl; // 690

  std::vector<EntityTree*> forest;

  int success_num = 0;
  std::cout << "build tree..." << std::endl;
  for (std::string root : root_list){
    EntityTree * new_tree = new EntityTree(root, data);
    forest.push_back(new_tree);
    success_num++;
    // std::cout << "tree: " << success_num << std::endl;
    // if (success_num > 50) break;
  }

  std::cout << "build tree success, the length of forest: " << success_num << std::endl;

  // EntityInfo * info = cuckoofilter::addr_map["骨科"];
  // EntityAddr * addr = info->head;
  // int cnt = 0;
  // while (addr != NULL){
  //   cnt++;
  //   addr = addr->next;
  // }
  // std::cout << "骨科" << ": " << cnt << std::endl;

  CuckooFilter<EntityStruct, 12> filter(3148);
  size_t num_inserted = 0;
  for (auto node : cuckoofilter::addr_map){
    num_inserted++;
    if (filter.Add({node.first}, node.second) != cuckoofilter::Ok) {
      std::cout << "add failed: " << node.first << std::endl;
      break;
    }
  }

  std::cout << "inserted number: " << num_inserted << std::endl;

  int M = 1024;
  std::vector<std::string> str_v = {"消化内科", "骨科", "肌电图室", "特检科", "肺功能室", "呼吸科", "支纤镜室", "直交流感应电疗"};

  std::cout << std::endl;
  std::cout << "the number of search to try: " << str_v.size()*(M+1) << std::endl;

  {
    EntityInfo * info;
    std::cout << std::endl;
    std::cout << "test using nothing: " << std::endl;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i=0;i<=M;i++)for(std::string test_str : str_v){
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "time: " << duration.count() << " s" << std::endl;
  }

  {
    EntityInfo * info;
    std::cout << std::endl;
    std::cout << "test using addr_map<>: " << std::endl;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i=0;i<=M;i++)for(std::string test_str : str_v){
      info = cuckoofilter::addr_map[test_str];
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "time: " << duration.count() << " s" << std::endl;
  }

  {
    EntityInfo * info;
    std::cout << std::endl;
    std::cout << "test using cuckoo filter: " << std::endl;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i=0;i<=M;i++)for(std::string test_str : str_v){
      info = filter.Extract({test_str});
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "time: " << duration.count() << " s" << std::endl;
  }

  filter.Sort(); // 排序

  {
    EntityInfo * info;
    std::cout << std::endl;
    std::cout << "test using cuckoo filter after sorting: " << std::endl;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i=0;i<=M;i++)for(std::string test_str : str_v){
      info = filter.Extract({test_str});
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "time: " << duration.count() << " s" << std::endl;
  }

  std::cout << std::endl;

  std::cout << "bucket_count of map_addr: " << cuckoofilter::addr_map.bucket_count() << std::endl;

  return 0;
}
