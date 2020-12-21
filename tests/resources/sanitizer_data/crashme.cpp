/*
 * Copyright (c) 2020 Tamas Keri.
 * Copyright (c) 2020 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <vector>

int global_array[100] = {-1};

volatile int *p = 0;

using namespace std;

void double_free() {
    char* ptr = (char*) malloc(sizeof(char));

    *ptr = 'a';
    free(ptr);
    free(ptr);
}

void global_buffer_overflow(int overflow) {
    int gbo = global_array[100 + overflow];
}

void heap_buffer_overflow(int overflow) {
    char* arr = (char*) malloc(10);
    char hbo = arr[10 + overflow];
}

long container_overflow() {
    vector<long> v;
    v.push_back(0);
    v.push_back(1);
    v.push_back(2);
    assert(v.capacity() >= 4);
    assert(v.size() == 3);
    long *p = &v[0];
    // Here the memory is accessed inside a heap-allocated buffer
    // but outside of the region `[v.begin(), v.end())`.
    return p[3];  // OOPS.
    // v[3] could be detected by simple checks in std::vector.
    // *(v.begin()+3) could be detected by a mighty debug iterator
    // (&v[0])[3] can only be detected with AddressSanitizer or similar.
}

void heap_use_after_free() {
    int *array = new int[100];
    delete [] array;

    int huaf = array[1];
}

void null_point_deref() {
    char buf[255];
    char* ptr = NULL;

    strcpy(ptr, buf);
}

void stack_buffer_overflow(int overflow) {
    int stack_array[100];
    stack_array[1] = 0;
    int sbo = stack_array[100 + overflow];
}

void stack_overflow() {
    stack_overflow();
}

void stack_use_after_scope() {
    {
        int x = 0;
        p = &x;
    }
    *p = 5;
}

void undefined_shifts() {
    int32_t i = 32;
    i <<= 30;
}

void signed_integer_overflow() {
    int32_t k = 0x7fffffff;
    k += 1;
}

void division_by_zero(int x) {
    int i = x / (x - x);
}

void null_deref_read() {
    int *p = NULL;
    printf("%d", *p);
}

void null_deref_write() {
    int *p = NULL;
    *p = 1;
}

int main(int argc, char **argv) {
    if (argc == 2) {
        string crashtype = string(argv[1]);
        if (crashtype == "division-by-zero") {
            division_by_zero(argc);
        } else if (crashtype == "null-deref-read") {
            null_deref_read();
        } else if (crashtype == "null-deref-write") {
            null_deref_write();
        } else if (crashtype == "double-free") {
            double_free();
        } else if (crashtype == "global-buffer-overflow") {
            global_buffer_overflow(argc);
        } else if (crashtype == "heap-buffer-overflow") {
            heap_buffer_overflow(argc);
        } else if (crashtype == "heap-use-after-free") {
            heap_use_after_free();
        } else if (crashtype == "null-pointer-dereference") {
            null_point_deref();
        } else if (crashtype == "shifts") {
            undefined_shifts();
        } else if (crashtype == "stack-buffer-overflow") {
            stack_buffer_overflow(argc);
        } else if (crashtype == "stack-overflow") {
            stack_overflow();
        } else if (crashtype == "stack-use-after-scope") {
            stack_use_after_scope();
        } else if (crashtype == "signed-integer-overflow") {
            signed_integer_overflow();
        } else if (crashtype == "container-overflow") {
            container_overflow();
        } else {
            cerr << "Invalid param!" << endl;
        }
    } else {
        cerr << "Invalid param number!" << endl;
    }
    return 0;
}
