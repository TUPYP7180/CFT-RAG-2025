#ifndef CUCKOO_FILTER_SINGLE_TABLE_H_
#define CUCKOO_FILTER_SINGLE_TABLE_H_

#include <assert.h>

#include <sstream>

#include "bitsutil.h"
#include "debug.h"
#include "printutil.h"
#include "node.h"

namespace cuckoofilter {

// the most naive table implementation: one huge bit array
template <size_t bits_per_tag>
class SingleTable {
  static const size_t kTagsPerBucket = 4;
  static const size_t kBytesPerBucket =
      (bits_per_tag * kTagsPerBucket + 7) >> 3;
  static const uint32_t kTagMask = (1ULL << bits_per_tag) - 1;
  // NOTE: accomodate extra buckets if necessary to avoid overrun
  // as we always read a uint64
  static const size_t kPaddingBuckets =
    ((((kBytesPerBucket + 7) / 8) * 8) - 1) / kBytesPerBucket;

  struct Bucket {
    char bits_[kBytesPerBucket];
    EntityInfo * info_[4];
  } __attribute__((__packed__));

  // using a pointer adds one more indirection
  Bucket *buckets_;
  size_t num_buckets_;

 public:
  explicit SingleTable(const size_t num) : num_buckets_(num) {
    buckets_ = new Bucket[num_buckets_ + kPaddingBuckets];
    memset(buckets_, 0, sizeof(Bucket) * (num_buckets_ + kPaddingBuckets));
  }

  ~SingleTable() { 
    delete[] buckets_;
  }

  size_t NumBuckets() const {
    return num_buckets_;
  }

  size_t SizeInBytes() const { 
    return kBytesPerBucket * num_buckets_; 
  }

  size_t SizeInTags() const { 
    return kTagsPerBucket * num_buckets_; 
  }

  std::string Info() const {
    std::stringstream ss;
    ss << "SingleHashtable with tag size: " << bits_per_tag << " bits \n";
    ss << "\t\tAssociativity: " << kTagsPerBucket << "\n";
    ss << "\t\tTotal # of rows: " << num_buckets_ << "\n";
    ss << "\t\tTotal # slots: " << SizeInTags() << "\n";
    return ss.str();
  }

  // read tag from pos(i,j)
  inline uint32_t ReadTag(const size_t i, const size_t j, EntityInfo ** result) const {
    
    *result = buckets_[i].info_[j];

    const char *p = buckets_[i].bits_;
    uint32_t tag;
    /* following code only works for little-endian */
    if (bits_per_tag == 2) {
      tag = *((uint8_t *)p) >> (j * 2);
    } else if (bits_per_tag == 4) {
      p += (j >> 1);
      tag = *((uint8_t *)p) >> ((j & 1) << 2);
    } else if (bits_per_tag == 8) {
      p += j;
      tag = *((uint8_t *)p);
    } else if (bits_per_tag == 12) {
      p += j + (j >> 1);
      tag = *((uint16_t *)p) >> ((j & 1) << 2);
    } else if (bits_per_tag == 16) {
      p += (j << 1);
      tag = *((uint16_t *)p);
    } else if (bits_per_tag == 32) {
      tag = ((uint32_t *)p)[j];
    }
    return tag & kTagMask;
  }

  // write tag to pos(i,j)
  inline void WriteTag(const size_t i, const size_t j, const uint32_t t, EntityInfo * info) {

    // std::cout << "j: " << j << std::endl;
    // std::cout << temp_info << std::endl;
    buckets_[i].info_[j] = info; // 将链表存到桶内

    char *p = buckets_[i].bits_;
    uint32_t tag = t & kTagMask;
    /* following code only works for little-endian */
    if (bits_per_tag == 2) {
      *((uint8_t *)p) |= tag << (2 * j);
    } else if (bits_per_tag == 4) {
      p += (j >> 1);
      if ((j & 1) == 0) {
        *((uint8_t *)p) &= 0xf0;
        *((uint8_t *)p) |= tag;
      } else {
        *((uint8_t *)p) &= 0x0f;
        *((uint8_t *)p) |= (tag << 4);
      }
    } else if (bits_per_tag == 8) {
      ((uint8_t *)p)[j] = tag;
    } else if (bits_per_tag == 12) {
      p += (j + (j >> 1));
      if ((j & 1) == 0) {
        ((uint16_t *)p)[0] &= 0xf000;
        ((uint16_t *)p)[0] |= tag;
      } else {
        ((uint16_t *)p)[0] &= 0x000f;
        ((uint16_t *)p)[0] |= (tag << 4);
      }
    } else if (bits_per_tag == 16) {
      ((uint16_t *)p)[j] = tag;
    } else if (bits_per_tag == 32) {
      ((uint32_t *)p)[j] = tag;
    }
  }

  inline void SortTag() {
    
    
    for (size_t i=0;i<num_buckets_;i++){

      int key = 0;

      Bucket * bucket_i = buckets_+i;

      EntityInfo * p0 = bucket_i->info_[0];
      EntityInfo * p1 = bucket_i->info_[1];
      EntityInfo * p2 = bucket_i->info_[2];
      EntityInfo * p3 = bucket_i->info_[3];

      for (size_t j = 0; j < kTagsPerBucket; j++) {
        int bubble_key = 0;
        for (size_t k = kTagsPerBucket-1; k > j; k--){

          if (bucket_i->info_[j] != NULL && bucket_i->info_[k] != NULL
          && bucket_i->info_[j]->temperature < bucket_i->info_[k]->temperature){
            bubble_key = 1;
            key = 1;
            EntityInfo * info_j = bucket_i->info_[j];
            EntityInfo * info_k = bucket_i->info_[k];
            EntityInfo * r;
            uint32_t tag_j = ReadTag(i, j, &r);
            uint32_t tag_k = ReadTag(i, k, &r);

            WriteTag(i, j, tag_k, info_k);
            WriteTag(i, k, tag_j, info_j);

          }
        }
        if (!bubble_key) break;
      }

      if (key) {
        
        // std::cout << p0 << std::endl;
        // std::cout << p1 << std::endl;
        // std::cout << p2 << std::endl;
        // std::cout << p3 << std::endl;

        // std::cout << bucket_i->info_[0] << std::endl;
        // std::cout << bucket_i->info_[1] << std::endl;
        // std::cout << bucket_i->info_[2] << std::endl;
        // std::cout << bucket_i->info_[3] << std::endl;

        // for (int i=0;i<3;i++){
        //   if (bucket_i->info_[i] != NULL){
        //     std::cout << bucket_i->info_[i]->temperature << std::endl;
        //     std::cout << bucket_i->info_[i]->head->addr->get_entity() << std::endl;
        //   }
        // }

      }

    }

  }

  inline bool FindTagInBuckets(const size_t i1, const size_t i2,
                               const uint32_t tag) const {
    const char *p1 = buckets_[i1].bits_;
    const char *p2 = buckets_[i2].bits_;

    uint64_t v1 = *((uint64_t *)p1);
    uint64_t v2 = *((uint64_t *)p2);

    // caution: unaligned access & assuming little endian
    if (bits_per_tag == 4 && kTagsPerBucket == 4) {
      return hasvalue4(v1, tag) || hasvalue4(v2, tag);
    } else if (bits_per_tag == 8 && kTagsPerBucket == 4) {
      return hasvalue8(v1, tag) || hasvalue8(v2, tag);
    } else if (bits_per_tag == 12 && kTagsPerBucket == 4) {
      return hasvalue12(v1, tag) || hasvalue12(v2, tag);
    } else if (bits_per_tag == 16 && kTagsPerBucket == 4) {
      return hasvalue16(v1, tag) || hasvalue16(v2, tag);
    } else {
      for (size_t j = 0; j < kTagsPerBucket; j++) {
        EntityInfo * r;
        if ((ReadTag(i1, j, &r) == tag) || (ReadTag(i2, j, &r) == tag)) {
          return true;
        }
      }
      return false;
    }
  }

  inline EntityInfo * FindInfoInBuckets(const size_t i1, const size_t i2,
                               const uint32_t tag) const {
    for (size_t j = 0; j < kTagsPerBucket; j++) {
      EntityInfo * r;
      // std::cout << "r:" << r << std::endl;
      if ((ReadTag(i1, j, &r) == tag)){
        // std::cout << r << std::endl;
        r->temperature++;
        return r;
      }else if (ReadTag(i2, j, &r) == tag) {
        // std::cout << r << std::endl;
        r->temperature++;
        return r;
      }
    }
    return NULL;
  }

  inline bool FindTagInBucket(const size_t i, const uint32_t tag) const {
    // caution: unaligned access & assuming little endian
    if (bits_per_tag == 4 && kTagsPerBucket == 4) {
      const char *p = buckets_[i].bits_;
      uint64_t v = *(uint64_t *)p;  // uint16_t may suffice
      return hasvalue4(v, tag);
    } else if (bits_per_tag == 8 && kTagsPerBucket == 4) {
      const char *p = buckets_[i].bits_;
      uint64_t v = *(uint64_t *)p;  // uint32_t may suffice
      return hasvalue8(v, tag);
    } else if (bits_per_tag == 12 && kTagsPerBucket == 4) {
      const char *p = buckets_[i].bits_;
      uint64_t v = *(uint64_t *)p;
      return hasvalue12(v, tag);
    } else if (bits_per_tag == 16 && kTagsPerBucket == 4) {
      const char *p = buckets_[i].bits_;
      uint64_t v = *(uint64_t *)p;
      return hasvalue16(v, tag);
    } else {
      for (size_t j = 0; j < kTagsPerBucket; j++) {
        EntityInfo * r;
        if (ReadTag(i, j, &r) == tag) {
          return true;
        }
      }
      return false;
    }
  }

  inline bool DeleteTagFromBucket(const size_t i, const uint32_t tag) {
    for (size_t j = 0; j < kTagsPerBucket; j++) {
      EntityInfo * r;
      if (ReadTag(i, j, &r) == tag) {
        assert(FindTagInBucket(i, tag) == true);
        WriteTag(i, j, 0, NULL);
        return true;
      }
    }
    return false;
  }

  inline bool InsertTagToBucket(const size_t i, const uint32_t tag, EntityInfo * info,
                                const bool kickout, uint32_t &oldtag, EntityInfo ** oldInfo) {
    for (size_t j = 0; j < kTagsPerBucket; j++) {
      EntityInfo * r;
      if (ReadTag(i, j, &r) == 0) {
        WriteTag(i, j, tag, info);
        return true;
      }
    }
    if (kickout) { // 要踢了
      size_t r = rand() % kTagsPerBucket;
      EntityInfo * oldInfo_;
      oldtag = ReadTag(i, r, &oldInfo_);
      *oldInfo = oldInfo_;
      WriteTag(i, r, tag, info);
    }
    return false;
  }

  inline size_t NumTagsInBucket(const size_t i) const {
    size_t num = 0;
    for (size_t j = 0; j < kTagsPerBucket; j++) {
      EntityInfo * r;
      if (ReadTag(i, j, &r) != 0) {
        num++;
      }
    }
    return num;
  }
};
}  // namespace cuckoofilter
#endif  // CUCKOO_FILTER_SINGLE_TABLE_H_
