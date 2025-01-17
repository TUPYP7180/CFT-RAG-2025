#ifndef CUCKOO_FILTER_CUCKOO_FILTER_H_
#define CUCKOO_FILTER_CUCKOO_FILTER_H_

#include <assert.h>
#include <algorithm>
#include <string>
#include "debug.h"
#include "hashutil.h"
#include "packedtable.h"
#include "printutil.h"
#include "singletable.h"
#include "node.h"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include <chrono>
#include <iomanip>

namespace py = pybind11;

namespace cuckoofilter {
// status returned by a cuckoo filter operation
enum Status {
  Ok = 0,
  NotFound = 1,
  NotEnoughSpace = 2,
  NotSupported = 3,
};

// maximum number of cuckoo kicks before claiming failure
const size_t kMaxCuckooCount = 500;

// A cuckoo filter class exposes a Bloomier filter interface,
// providing methods of Add, Delete, Contain. It takes three
// template parameters:
//   ItemType:  the type of item you want to insert
//   bits_per_item: how many bits each item is hashed into
//   TableType: the storage of table, SingleTable by default, and
// PackedTable to enable semi-sorting
template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType = SingleTable,
          typename HashFamily = TwoIndependentMultiplyShift>
class CuckooFilter {
  // Storage of items
  TableType<bits_per_item> *table_;

  // Number of items stored
  size_t num_items_;

  typedef struct {
    size_t index;
    uint32_t tag;
    EntityInfo * info;
    bool used;
  } VictimCache;

  VictimCache victim_;

  HashFamily hasher_;

  inline size_t IndexHash(uint32_t hv) const {
    // table_->num_buckets is always a power of two, so modulo can be replaced
    // with
    // bitwise-and:
    return hv & (table_->NumBuckets() - 1);
  }

  inline uint32_t TagHash(uint32_t hv) const {
    uint32_t tag;
    tag = hv & ((1ULL << bits_per_item) - 1);
    tag += (tag == 0);
    return tag;
  }

  inline void GenerateIndexTagHash(const ItemType& item, size_t* index,
                                   uint32_t* tag) const {
    const uint64_t hash = hasher_(item);
    *index = IndexHash(hash >> 32);
    *tag = TagHash(hash);
  }

  inline size_t AltIndex(const size_t index, const uint32_t tag) const {
    // NOTE(binfan): originally we use:
    // index ^ HashUtil::BobHash((const void*) (&tag), 4)) & table_->INDEXMASK;
    // now doing a quick-n-dirty way:
    // 0x5bd1e995 is the hash constant from MurmurHash2
    return IndexHash((uint32_t)(index ^ (tag * 0x5bd1e995)));
  }

  Status AddImpl(const size_t i, const uint32_t tag, EntityInfo * info);

  // load factor is the fraction of occupancy
  double LoadFactor() const { return 1.0 * Size() / table_->SizeInTags(); }

  double BitsPerItem() const { return 8.0 * table_->SizeInBytes() / Size(); }

 public:
  explicit CuckooFilter(const size_t max_num_keys) : num_items_(0), victim_(), hasher_() {
    size_t assoc = 4;
    size_t num_buckets = upperpower2(std::max<uint64_t>(1, max_num_keys / assoc));
    double frac = (double)max_num_keys / num_buckets / assoc;
    if (frac > 0.96) {
      num_buckets <<= 1;
    }
    victim_.used = false;
    std::cout << "num_buckets: " << num_buckets << std::endl;
    table_ = new TableType<bits_per_item>(num_buckets);
  }

  ~CuckooFilter() { delete table_; }

  // Add an item to the filter.
  Status Add(const ItemType &item, EntityInfo * info);

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

  void BuildTree(const size_t max_tree_num, const size_t max_node_num) {

    std::cout << "build in block link list......" << std::endl;

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
    int node_num = 0;
    for (std::string root : root_list){
      EntityTree * new_tree = new EntityTree(root, data);

      int cc = new_tree->count_num();
      if (cc+node_num > max_node_num) break;
      node_num += cc;

      forest.push_back(new_tree);
      success_num++;
      if (success_num == max_tree_num){break;}
    }

    std::cout << "build tree success, the length of forest: " << success_num << ", the number of node: " << node_num << std::endl;
    
    size_t num_inserted = 0;
    for (auto node : cuckoofilter::addr_map){
      num_inserted++;
      if (this->Add({node.first}, node.second) != cuckoofilter::Ok) {
        std::cout << "add failed: " << node.first << std::endl;
        break;
      }
    }
    std::cout << "inserted number: " << num_inserted << std::endl;
  }

  // Report if the item is inserted, with false positive rate.
  Status Contain(const ItemType &item) const;

  std::string Extract(const ItemType &item) const;

  void Sort();

  // Delete an key from the filter
  Status Delete(const ItemType &item);

  /* methods for providing stats  */
  // summary infomation
  std::string Info() const;

  // number of current inserted items;
  size_t Size() const { return num_items_; }

  // size of the filter in bytes.
  size_t SizeInBytes() const { return table_->SizeInBytes(); }
};

template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType, typename HashFamily>
Status CuckooFilter<ItemType, bits_per_item, TableType, HashFamily>::Add(
    const ItemType &item, EntityInfo * info) {

  // std::cout << "info: " << info << std::endl;
  // std::cout << "item: " << item.content << std::endl;

  size_t i;
  uint32_t tag;

  if (victim_.used) {
    return NotEnoughSpace;
  }

  GenerateIndexTagHash(item, &i, &tag);
  return AddImpl(i, tag, info);
}

template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType, typename HashFamily>
Status CuckooFilter<ItemType, bits_per_item, TableType, HashFamily>::AddImpl(
    const size_t i, const uint32_t tag, EntityInfo * info) {
  size_t curindex = i;
  uint32_t curtag = tag;
  uint32_t oldtag;
  EntityInfo * curInfo = info;
  EntityInfo * oldInfo;

  for (uint32_t count = 0; count < kMaxCuckooCount; count++) {
    bool kickout = count > 0;
    oldtag = 0;
    if (table_->InsertTagToBucket(curindex, curtag, curInfo, kickout, oldtag, &oldInfo)) {
      num_items_++;
      return Ok;
    }
    if (kickout) {
      curtag = oldtag;
      curInfo = oldInfo;
    }
    curindex = AltIndex(curindex, curtag);
  }

  victim_.index = curindex;
  victim_.tag = curtag;
  victim_.used = true;
  victim_.info = curInfo;

  return Ok;
}

template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType, typename HashFamily>
Status CuckooFilter<ItemType, bits_per_item, TableType, HashFamily>::Contain(
    const ItemType &key) const {
  bool found = false;
  size_t i1, i2;
  uint32_t tag;

  GenerateIndexTagHash(key, &i1, &tag);
  i2 = AltIndex(i1, tag);

  assert(i1 == AltIndex(i2, tag));

  found = victim_.used && (tag == victim_.tag) &&
          (i1 == victim_.index || i2 == victim_.index);

  if (found || table_->FindTagInBuckets(i1, i2, tag)) {
    return Ok;
  } else {
    return NotFound;
  }
}

template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType, typename HashFamily>
std::string CuckooFilter<ItemType, bits_per_item, TableType, HashFamily>::Extract(
const ItemType &key) const {

  // std::cout << "extract: " << key << std::endl;

  auto start = std::chrono::high_resolution_clock::now();

  bool found = false;
  size_t i1, i2;
  uint32_t tag;

  GenerateIndexTagHash(key, &i1, &tag);
  i2 = AltIndex(i1, tag);

  assert(i1 == AltIndex(i2, tag));

  found = victim_.used && (tag == victim_.tag) &&
          (i1 == victim_.index || i2 == victim_.index);

  

  if (found){
    // std::cout << 2 << std::endl;
    // std::cout << "cpp debug: " <<  victim_.info << std::endl;
    // std::cout << "cpp debug: " <<  victim_.info->temperature << std::endl;
    // std::cout << "cpp debug: " <<  victim_.info->head << std::endl;
    std::string result = "";
    EntityAddr * addr = victim_.info->head;
    while (addr != NULL){
      
      if (addr->addr1 != NULL) result += addr->addr1->get_context();
      if (addr->addr2 != NULL) result += addr->addr2->get_context();
      if (addr->addr3 != NULL) result += addr->addr3->get_context();
      
      addr = addr->next;
    } 
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    // std::cout << std::fixed << std::setprecision(12);
    // std::cout << "extract by cuckoo filter: " << duration.count() << " s" << std::endl;
    return result;
  }else {
    // std::cout << 3 << std::endl;
    // std::cout << "cpp debug: " <<  table_->FindInfoInBuckets(i1, i2, tag) << std::endl;
    // std::cout << "cpp debug: " << table_->FindInfoInBuckets(i1, i2, tag)->temperature  << std::endl;
    // std::cout << "cpp debug: " << table_->FindInfoInBuckets(i1, i2, tag)->head  << std::endl;
    std::string result = "";
    EntityInfo * r0;
    EntityAddr * addr;
    if (r0 = table_->FindInfoInBuckets(i1, i2, tag)){
      addr = r0->head;
    }else return "";
    while (addr != NULL){

      if (addr->addr1 != NULL) result += addr->addr1->get_context();
      if (addr->addr2 != NULL) result += addr->addr2->get_context();
      if (addr->addr3 != NULL) result += addr->addr3->get_context();
      
      addr = addr->next;
    } 
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    // std::cout << std::fixed << std::setprecision(12);
    // std::cout << "extract by cuckoo filter: " << duration.count() << " s" << std::endl;
    return result;
  }

}

template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType, typename HashFamily>
void CuckooFilter<ItemType, bits_per_item, TableType, HashFamily>::Sort(){

  table_->SortTag();

}


template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType, typename HashFamily>
Status CuckooFilter<ItemType, bits_per_item, TableType, HashFamily>::Delete(
    const ItemType &key) {
  size_t i1, i2;
  uint32_t tag;

  GenerateIndexTagHash(key, &i1, &tag);
  i2 = AltIndex(i1, tag);

  if (table_->DeleteTagFromBucket(i1, tag)) {
    num_items_--;
    goto TryEliminateVictim;
  } else if (table_->DeleteTagFromBucket(i2, tag)) {
    num_items_--;
    goto TryEliminateVictim;
  } else if (victim_.used && tag == victim_.tag &&
             (i1 == victim_.index || i2 == victim_.index)) {
    // num_items_--;
    victim_.used = false;
    return Ok;
  } else {
    return NotFound;
  }
TryEliminateVictim:
  if (victim_.used) {
    victim_.used = false;
    size_t i = victim_.index;
    uint32_t tag = victim_.tag;
    EntityInfo * info = victim_.info;
    AddImpl(i, tag, info);
  }
  return Ok;
}

template <typename ItemType, size_t bits_per_item,
          template <size_t> class TableType, typename HashFamily>
std::string CuckooFilter<ItemType, bits_per_item, TableType, HashFamily>::Info() const {
  std::stringstream ss;
  ss << "CuckooFilter Status:\n"
     << "\t\t" << table_->Info() << "\n"
     << "\t\tKeys stored: " << Size() << "\n"
     << "\t\tLoad factor: " << LoadFactor() << "\n"
     << "\t\tHashtable size: " << (table_->SizeInBytes() >> 10) << " KB\n";
  if (Size() > 0) {
    ss << "\t\tbit/key:   " << BitsPerItem() << "\n";
  } else {
    ss << "\t\tbit/key:   N/A\n";
  }
  return ss.str();
}
}  // namespace cuckoofilter
#endif  // CUCKOO_FILTER_CUCKOO_FILTER_H_
