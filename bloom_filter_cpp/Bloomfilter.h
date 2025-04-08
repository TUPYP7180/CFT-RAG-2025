#ifndef BLOOMFILTER_H
#define BLOOMFILTER_H

#include <openssl/md5.h>

#include <bitset>
#include <memory>

#include <iostream>

class Bloomfilter
{
public:
	Bloomfilter(size_t hash_func_count = 4)
	: hash_function_count(hash_func_count),
	  object_count_(0),
	  MD5_hash_result_buffer(std::make_unique<unsigned char[]>(MD5_result_size_bytes))
	{
    	// std::cout << "MD5 buffer allocated at: " << static_cast<void*>(MD5_hash_result_buffer.get()) << std::endl;
		if(0 == hash_func_count)
		{
			throw std::invalid_argument("Bloomfilter could not be initialized: hash_func_count must be larger than 0");
		}
		if(MD5_result_size_bytes < hash_function_count * bytes_per_hash_function)
		{
			throw std::invalid_argument("Bloomfilter could not be initialized: hash_func_count too large, hash_func_count *  bytes_per_hash_function must be smaller or equal to MD5_result_size_bytes");
		}
		// std::cout << "Bloomfilter instance address: " << this << std::endl;
	}

	void insert(const std::string& object)
	{
		// std::cout << "insert(const std::string& object)" << std::endl;
		// std::cout << "Bloomfilter instance address: " << this << std::endl;
		// std::cout << "MD5 buffer address in insert: " << static_cast<void*>(MD5_hash_result_buffer.get()) << std::endl;
    	// if (MD5_hash_result_buffer == nullptr) {
        // 	std::cerr << "MD5 buffer is null in insert!" << std::endl;
        // 	return;
    	// }
		hash(object);
		const uint16_t* const object_hashes = reinterpret_cast<const uint16_t * const>(MD5_hash_result_buffer.get());

		for (size_t i = 0; i < hash_function_count; i++)
		{
			const uint16_t index_to_set = object_hashes[i];
			bloomfilter_store_[index_to_set] = true;
		}
		++object_count_;
	}

	void clear()
	{
		bloomfilter_store_.reset();
		object_count_ = 0;
	}

	bool contains(const std::string& object) const
	{
		std::cout << "Bloomfilter contains: " << object << std::endl;
		hash(object);
		const uint16_t* const object_hashes = reinterpret_cast<const uint16_t * const>(MD5_hash_result_buffer.get());		

		for (size_t i = 0; i < hash_function_count; i++)
		{
			const uint16_t index_to_get = object_hashes[i];
			if (!bloomfilter_store_[index_to_get]){
				std::cout << "Bloomfilter contains: " << object << "false" << std::endl;
				return false;
			} 
		}
		std::cout << "Bloomfilter contains: " << object << "true" << std::endl;
		return true;
	}

	size_t object_count() const
	{
		return object_count_;
	}

	bool empty() const
	{
		return 0 == object_count();
	}

private:

	// Size of the MD5 hash result, always fixed to 16 bytes.
	static constexpr size_t MD5_result_size_bytes = 16;
	
	// Size of the bloom filter state in bits (2^16).
	static constexpr size_t bloomfilter_store_size = 65536;

	// Set to 2 bytes so all bloom filter bits can be indexed (2^16 different values).
	static constexpr size_t bytes_per_hash_function = 2;

	static_assert(1 << (bytes_per_hash_function*8) >= bloomfilter_store_size,
		"Not all Bloom filter bits indexable, increase bytes_per_hash_function or decrease bloomfilter_store_size");

	void hash(const std::string& val) const
	{
		// std::cout << "Computing hash for: " << val << std::endl;
		const unsigned char* const md5_input_val = reinterpret_cast<const unsigned char*>(val.data());
		// std::cout << "md5_input_val." << std::endl;
		const size_t md5_input_length = val.length();
		// std::cout << "md5_input_length." << md5_input_length << std::endl;
		// std::cout << "MD5 buffer address: " << static_cast<void*>(MD5_hash_result_buffer.get()) << std::endl;
		// std::cout << "MD5 buffer size: " << MD5_result_size_bytes << std::endl;
		MD5(md5_input_val, md5_input_length, MD5_hash_result_buffer.get());
		// std::cout << "Hash computed successfully." << std::endl;
	}

// Number of hash functions to use when hashing objects (cannot be larger than MD5_result_size_bytes/bytes_per_hash_function).
	const size_t hash_function_count;

	std::bitset<bloomfilter_store_size> bloomfilter_store_;
	size_t object_count_;

	const std::unique_ptr<unsigned char[]> MD5_hash_result_buffer;
};

#endif // BLOOMFILTER_H
