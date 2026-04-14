#ifndef FINGERPRINT_H
#define FINGERPRINT_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    unsigned char *data;
    long size;
} Buffer;

Buffer buffer_create(long size);
void buffer_free(Buffer *buf);
Buffer get_file_contents(const char *file_path);
long get_file_size(FILE *file);
uint32_t compute_hash(const Buffer *buffer);
int is_whitespace_character(unsigned char b);
uint32_t compute_normalized_length(const Buffer *buffer);

#endif
