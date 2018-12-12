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
