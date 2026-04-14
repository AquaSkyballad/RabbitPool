#include "fingerprint.h"
#include <string.h>

Buffer buffer_create(long size) {
    Buffer buf;
    buf.size = size;
    if (size > 0) {
        buf.data = (unsigned char *)malloc((size_t)size);
        if (buf.data == NULL) {
            buf.size = 0;
        } else {
            memset(buf.data, 0, (size_t)size);
        }
    } else {
        buf.data = (unsigned char *)malloc(1);
        if (buf.data == NULL) {
            buf.size = 0;
        } else {
            buf.size = 0;
        }
    }
    return buf;
}

void buffer_free(Buffer *buf) {
    if (buf != NULL && buf->data != NULL) {
        free(buf->data);
        buf->data = NULL;
        buf->size = 0;
    }
}

Buffer get_file_contents(const char *file_path) {
    FILE *file = fopen(file_path, "rb");
    if (file == NULL) {
        Buffer empty;
        empty.data = NULL;
        empty.size = 0;
        return empty;
    }

    long buffer_size = get_file_size(file);

    Buffer buffer = buffer_create(buffer_size);
    if (buffer.data == NULL && buffer_size > 0) {
        fclose(file);
        return buffer;
    }

    if (buffer_size > 0) {
        size_t read = fread(buffer.data, 1, (size_t)buffer_size, file);
        if ((long)read != buffer_size) {
            buffer_free(&buffer);
            fclose(file);
            Buffer empty;
            empty.data = NULL;
            empty.size = 0;
            return empty;
        }
    }

    fclose(file);
    return buffer;
}

long get_file_size(FILE *file) {
    fseek(file, 0, SEEK_END);
    long size = ftell(file);
    fseek(file, 0, SEEK_SET);
    return size;
}

uint32_t compute_hash(const Buffer *buffer) {
    const uint32_t multiplex = 1540483477;
    const uint32_t length = (uint32_t)buffer->size;
    uint32_t num1 = length;

    num1 = compute_normalized_length(buffer);

    uint32_t num2 = (uint32_t)1 ^ num1;
    uint32_t num3 = 0;
    uint32_t num4 = 0;

    for (uint32_t index = 0; index < length; ++index) {
        unsigned char b = buffer->data[index];

        if (!is_whitespace_character(b)) {
            num3 |= (uint32_t)b << num4;
            num4 += 8;
            if (num4 == 32) {
                uint32_t num6 = num3 * multiplex;
                uint32_t num7 = (num6 ^ num6 >> 24) * multiplex;
                num2 = num2 * multiplex ^ num7;
                num3 = 0;
                num4 = 0;
            }
        }
    }

    if (num4 > 0) {
        num2 = (num2 ^ num3) * multiplex;
    }

    uint32_t num6 = (num2 ^ num2 >> 13) * multiplex;

    return num6 ^ num6 >> 15;
}

uint32_t compute_normalized_length(const Buffer *buffer) {
    uint32_t num1 = 0;
    const uint32_t length = (uint32_t)buffer->size;

    for (uint32_t index = 0; index < length; ++index) {
        if (!is_whitespace_character(buffer->data[index])) {
            ++num1;
        }
    }

    return num1;
}

int is_whitespace_character(unsigned char b) {
    return b == 9 || b == 10 || b == 13 || b == 32;
}
