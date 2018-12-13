/*
*   The MIT License (MIT)

*   Copyright (c) 2018 Wei Shi

*   Permission is hereby granted, free of charge, to any person obtaining a copy
*   of this software and associated documentation files (the "Software"), to deal
*   in the Software without restriction, including without limitation the rights
*   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
*   copies of the Software, and to permit persons to whom the Software is
*   furnished to do so, subject to the following conditions:

*   The above copyright notice and this permission notice shall be included in all
*   copies or substantial portions of the Software.

*   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
*   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
*   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
*   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
*   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
*   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
*   SOFTWARE.
*/
#ifndef _ST_LOG_H__
#define _ST_LOG_H__

#include <iostream>
#include <string>
#include <string.h>

#ifdef DEBUG
    #define LogDebug(M, ...) fprintf(stdout, "[DEBUG] " M " (%s:%d) \n", ##__VA_ARGS__, __FILE__, __LINE__)
    #define LogInfo(M, ...) fprintf(stdout, "[INFO] " M " (%s:%d) \n", ##__VA_ARGS__, __FILE__, __LINE__)
    #define log_clean_errno() (errno == 0 ? "None" : strerror(errno))
    #define LogWarn(M, ...) fprintf(stdout, "[WARN] " M " (%s:%d: errno: %s)\n", ##__VA_ARGS__, __FILE__, __LINE__, log_clean_errno())
    #define LogError(M, ...) fprintf(stderr, "[ERROR] " M " (%s:%d: errno: %s)\n", ##__VA_ARGS__, __FILE__, __LINE__, log_clean_errno())
#else
    #define LogDebug(M, ...)
    #define LogInfo(M, ...) fprintf(stdout, "[INFO] " M "\n", ##__VA_ARGS__)
    #define log_clean_errno() (errno == 0 ? "None" : strerror(errno))
    #define LogWarn(M, ...) fprintf(stdout, "[WARN] " M " (errno: %s)\n", ##__VA_ARGS__, log_clean_errno())
    #define LogError(M, ...) fprintf(stderr, "[ERROR] " M " (errno: %s)\n", ##__VA_ARGS__,log_clean_errno())
#endif

#endif
