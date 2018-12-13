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
#include "BrutalPacking.h"

#include <unordered_map>

using namespace rapidjson;
using namespace std;


const char *BrutalPacking::POINTS = "points";
const char *BrutalPacking::AREA = "area";
const char *BrutalPacking::ROTATION = "rotation";
const char *BrutalPacking::X = "x";
const char *BrutalPacking::Y = "y";
const char *BrutalPacking::W = "w";
const char *BrutalPacking::H = "h";
const char *BrutalPacking::FILE_NAME = "file";

const char *BrutalPacking::KernelDetection = ""
        "__kernel void detection("
        "   __global uchar* map,"
        "   __global int2* canvas,"
        "   __global uchar* candidate,"
        "   __global int4* result,"
        "   const int width,"
        "   const int height,"
        "   const int w,"
        "   const int h,"
        "   const int size"
        "){"
        "__private int idx = get_global_id(0);"
        "if( idx < size){"
        "   __private int2 cache = canvas[idx];"
        "   __private int bbb = ((cache.x + w) < width);"
        "   bbb += ((cache.y + h) < height);"
        "   __private int sum = 0;"
        "   if(bbb == 2){"
        "       for(__private int y = 0; y < h; y++){"
        "           __private int offset = y * w;"
        "           __private int canvasOffset = (y + cache.y) * width + cache.x;"
        "           for(__private int x = 0; x < w; x++){"
        "               sum =  sum + map[canvasOffset + x] * candidate[offset + x];"
        "           }"
        "       }"
        "   }else{sum = 1;}"
        "   result[idx] = (int4)(cache.x, cache.y, (sum == 0), 0);"

        "}"
        "}";
//void BrutalPacking::detection(int idx, u_char* map, cl_int2* canvas, u_char* candidate, cl_int3* result,
//                              const int width, const int height, const int w, const int h, const int size){
//    if(idx < size){
//        cl_int2 cache = canvas[idx];
//        int ret = 1;
//        if(cache.s[0] + w < width && cache.s[1] + h < height){
//            for(int y = 0; y < h; y++){
//                int offset = y * w;
//                int canvasOffset = (y + cache.s[1]) * width + cache.s[0];
//                for(int x = 0; x < w; x++){
//                    if(candidate[offset + x] == 1 && map[canvasOffset + x] == 1){
//                        ret = 0;
//                    }
//                }
//            }
//        }else{
//            ret = 0;
//        }
//        result[idx].s[0] = cache.s[0];
//        result[idx].s[1] = cache.s[1];
//        result[idx].s[2] = ret;
//    }
//}

BrutalPacking::BrutalPacking(int size, int loopLimit):maxSize(size){
    assert(maxSize > 0);
    if(loopLimit > 0){
        _loopLimit= loopLimit;
    }else{
        _loopLimit= 1000;
    }
    LogInfo("Canvas max size is %d x %d, loop limit is %d", maxSize, maxSize, _loopLimit);
    intersections = nullptr;
    deviceInited = false;
    canvasHeight = canvasSize = 0;
    map.resize(maxSize * maxSize, 0);
    memset(map.data(), 0, sizeof(cl_uchar) * maxSize * maxSize);
}

BrutalPacking::~BrutalPacking() {
    if (intersections != nullptr) {
        delete intersections;
    }

    // == RELEASE OPEN CL ======
    for(int i = 0; i < _devicesCount; i++){
        if(deviceInited){
            if (_canvas_inputs[i] != NULL) {
                clReleaseMemObject(_canvas_inputs[i]);
            }
            if (_map_inputs[i] != NULL) {
                clReleaseMemObject(_map_inputs[i]);
            }
            if (_result_outputs[i] != NULL) {
                clReleaseMemObject(_result_outputs[i]);
            }
            if (_candidate_inputs[i] != NULL) {
                clReleaseMemObject(_candidate_inputs[i]);
            }
        }
        if(_programs[i] != NULL){
            clReleaseProgram(_programs[i]);
        }

        if(_kernels[i] != NULL){
            clReleaseKernel(_kernels[i]);
        }
        if(_commands[i] != NULL){
            clReleaseCommandQueue(_commands[i]);
        }

        if(_contexts[i] != NULL){
            clReleaseContext(_contexts[i]);
        }

        if(_workerThreads[i] != nullptr){
            delete _workerThreads[i];
        }
    }


}

bool BrutalPacking::initDevice() {
    //===================== OPEN CL SETUP ================

    cl_uint platformCount = 0;
    _cl_errs[0] = clGetPlatformIDs(NULL, NULL, &platformCount);
    LogInfo("There are %d platform available", platformCount);
    if(platformCount == 0){
        LogError("No platform available");
        return false;
    }
    cl_platform_id* platform_id = new cl_platform_id[platformCount];
    _cl_errs[0] = clGetPlatformIDs(platformCount, platform_id, NULL);
    if (_cl_errs[0] != CL_SUCCESS) {
        LogError("Error: Failed to get platforms\n");
        printCLError(_cl_errs[0]);
        return false;
    }
    _devicesCount = 0;
    _device_ids = new cl_device_id[10];
    cl_platform_id *platformDeviceRel = new cl_platform_id[10];

    char buf[256], buff2[256], vendor[256], platformName[256];
    for(int p = 0; p < platformCount; p ++){

        _cl_errs[0] = clGetPlatformInfo(platform_id[p], CL_PLATFORM_NAME, 256, platformName, NULL);
        if (_cl_errs[0] != CL_SUCCESS) {
            LogError("Error: Failed to get platforms %d info\n", p);
            printCLError(_cl_errs[0]);
            continue;
        }

        cl_uint deviceCount = 0;
        _cl_errs[0] = clGetDeviceIDs(platform_id[p], CL_DEVICE_TYPE_GPU, 0, NULL, &deviceCount);
        if (deviceCount > 0) {
            cl_device_id* device_ids = new cl_device_id[deviceCount];

            _cl_errs[0] = clGetDeviceIDs(platform_id[p], CL_DEVICE_TYPE_GPU, deviceCount, device_ids, NULL);

            if (_cl_errs[0] != CL_SUCCESS) {
                LogError("Error: Failed to get devices for platform %s!\n", platformName);
                printCLError(_cl_errs[0]);
                delete[] device_ids;
                continue;


            }
            else {
                LogInfo("There are %d devices avaliable for platform %s", deviceCount, platformName);
            }
            for (int i = 0; i < deviceCount; i++) {
                // lets skip GPU vendor from Intel for performance reason
                clGetDeviceInfo(device_ids[i], CL_DEVICE_NAME, 256, buf, NULL);
                clGetDeviceInfo(device_ids[i], CL_DEVICE_VERSION, 256, buff2, NULL);
                clGetDeviceInfo(device_ids[i], CL_DEVICE_VENDOR, 256, vendor, NULL);
                std::string vendorName = vendor;
                if (vendorName == "Intel") {
                    std::cout << "[INFO] Skip Using Device ID "<< device_ids[i] <<" : "<< buf << " support " << buff2 << " from Vendor " << vendor << " for platform " << platformName << std::endl;
                }
                else {
                    _device_ids[_devicesCount] = device_ids[i];
                    platformDeviceRel[_devicesCount] = platform_id[p];
                    std::cout << "[INFO] Using Device ID " << device_ids[i] << " : " << _devicesCount << " for " << buf << " support " << buff2 << " from Vendor " << vendor << " for platform " << platformName << std::endl;
                    _devicesCount++;
                }

            }
            delete[] device_ids;
        }else {
            LogInfo("There is no device available for platform %s", platformName);
        }

    }
    delete[] platform_id;
    LogInfo("We total have %d device available for processing", _devicesCount);

    _contexts = new cl_context[_devicesCount];
    _commands = new cl_command_queue[_devicesCount];
    _programs = new cl_program[_devicesCount];
    _kernels = new cl_kernel[_devicesCount];

    _map_inputs = new cl_mem[_devicesCount];
    _canvas_inputs = new cl_mem[_devicesCount];
    _candidate_inputs = new cl_mem[_devicesCount];
    _result_outputs = new cl_mem[_devicesCount];

    _locals = new size_t[_devicesCount];
    _workerThreads = new std::thread*[_devicesCount];

    for(int i = 0; i < _devicesCount;i ++) {
        _workerThreads[i] = nullptr;
        _contexts[i] = NULL;
        _commands[i] = NULL;
        _programs[i] = NULL;
        _kernels[i] = NULL;

        _map_inputs[i] = NULL;
        _canvas_inputs[i] = NULL;
        _candidate_inputs[i] = NULL;
        _result_outputs[i] = NULL;
        _locals[i] = 0;
    }

    for(int i = 0; i < _devicesCount;i ++){
        LogInfo("Creating context for devices %d",i);
        // Create a compute context
        cl_context_properties properioes[] = { CL_CONTEXT_PLATFORM, (cl_context_properties)platformDeviceRel[i], 0 };
        _contexts[i] = clCreateContext(properioes, 1, &_device_ids[i], NULL, NULL, &_cl_errs[i]);

        if (_cl_errs[i] != CL_SUCCESS) {
            LogError("Failed to create a compute context for device %d!\n", i);
            printCLError(_cl_errs[i]);
            return false;
        }
        // Create a command commands

        //

        _commands[i] = clCreateCommandQueue(_contexts[i], _device_ids[i], 0, &_cl_errs[i]);

        if (_cl_errs[i] != CL_SUCCESS) {
            LogError("Failed to create a command commands for device %d!\n", i);
            printCLError(_cl_errs[i]);
            return false;
        }

        // Create the compute program from the source buffer

        //

        _programs[i] = clCreateProgramWithSource(_contexts[i], 1, (const char **) &KernelDetection, NULL, &_cl_errs[i]);

        if (!_programs[i]) {
            LogError("Error: Failed to create compute programfor device %d!\n", i);
            printCLError(_cl_errs[i]);
            return false;
        }

        // Build the program executable

        //

        _cl_errs[i] = clBuildProgram(_programs[i], 0, NULL, NULL, NULL, NULL);

        if (_cl_errs[i] != CL_SUCCESS) {

            size_t len;

            char buffer[2048];

            LogError("Error: Failed to build program executable for device %d!\n",i);

            clGetProgramBuildInfo(_programs[i], _device_ids[i], CL_PROGRAM_BUILD_LOG, sizeof(buffer), buffer, &len);

            LogError("%s\n", buffer);

            return false;

        }

        // Create the compute kernel in the program we wish to run
        //

        _kernels[i] = clCreateKernel(_programs[i], "detection", &_cl_errs[i]);

        if (!_kernels[i] || _cl_errs[i] != CL_SUCCESS) {
            LogError("Error: Failed to create compute kernel for device %d\n", i);
            printCLError(_cl_errs[i]);
            return false;
        }

        _cl_errs[i] = clGetKernelWorkGroupInfo(_kernels[i], _device_ids[i], CL_KERNEL_WORK_GROUP_SIZE, sizeof(_locals[i]), &_locals[i], NULL);

        if (_cl_errs[i] != CL_SUCCESS) {
            LogError("Error: Failed to retrieve kernel work group info! %d for device %d\n", _cl_errs[i], i);
            printCLError(_cl_errs[i]);
            return false;
        } else {
            LogInfo("Local workgroup size: %d for deivce %d", (int) _locals[i], i);
        }
        _map_inputs[i] = clCreateBuffer(_contexts[i], CL_MEM_READ_ONLY, sizeof(cl_uchar) * maxSize * maxSize, NULL, &_cl_errs[i]);
        if (_cl_errs[i] != CL_SUCCESS) {
            LogError("Can not create map data in device %d",i);
            return false;
        }

    }
    delete[] platformDeviceRel;

    deviceInited = true;
    return true;
}

bool BrutalPacking::readPolygon(const char *str) {
    Document doc;
    doc.Parse(str);
    list<VectorInt2> tempList;
    for (SizeType i = 0; i < doc.Size(); i++) {
        rapidjson::Value &node = doc[i];
        if (node.HasMember(AREA)) {
            int area = node[AREA].GetInt();
            // lets insert into list
            bool flag = false;
            for (auto it = tempList.begin(); it != tempList.end(); it++) {
                if (area > it->v0) {
                    tempList.insert(it, VectorInt2(area, i));
                    flag = true;
                    break;
                }
            }
            if (!flag) {
                tempList.push_back(VectorInt2(area, i));
            }
        }
    }
    int counter = 0;
    for (auto it = tempList.begin(); it != tempList.end(); it++, counter++) {
        if (doc[it->v1].HasMember(POINTS)) {
            vector<VectorInt2> ps;
            rapidjson::Value &node = doc[it->v1][POINTS];
            for (SizeType j = 0; j < node.Size(); j++) {
                ps.push_back(VectorInt2(node[j][0].GetInt(), node[j][1].GetInt()));
            }
            //Debug("push poly %d", counter);
            shared_ptr<ResultInfo> re = make_shared<ResultInfo>();
            re->poly = make_shared<Poly>(ps);
//            rapidjson::Value &node2 = doc[it->v1][RECT];
//            re->x = node2[0].GetInt();
//            re->y = node2[1].GetInt();
//            re->w = node2[2].GetInt();
//            re->h = node2[3].GetInt();
//            re->rotation = doc[it->v1][ROTATION].GetInt();
//            re->rectArea = doc[it->v1][RECT_AREA].GetInt();
            re->area = doc[it->v1][AREA].GetInt();

            re->path = doc[it->v1][FILE_NAME].GetString();
//          if(re->area < 25){
//              LogInfo("Skip Image: %s, because area is too small %d", re->path.c_str(), re->area);
//              continue;
//          }
//            re->altPath = doc[it->v1][FILE_ALT_NAME].GetString();
            results.push_back(re);
        } else {
            LogError("Poly #%d has not points!, file name: %s", it->v1, doc[counter][FILE_NAME].GetString());
            return false;
        }
    }
    return true;
}

bool BrutalPacking::expandCanvas(const shared_ptr<Poly>& poly) {
    return (poly->getHeight() + canvas.size() < maxSize);
}

bool BrutalPacking::fillCanvas(const shared_ptr<Poly>& poly, const int x, const int y) {
    LogInfo("=============== Filling canvas for position %d, %d =============== ", x, y);
    const vector<VectorInt2>& slices = poly->getSlice();
    for (int j = y; j < slices.size() + y; j++) {
        int offset = j - y;
        if (j < canvas.size()) {
            bool filled = false;
            for (auto it = canvas[j].begin();it != canvas[j].end() && !filled ; it++) {
                if (it->isInRange(x + slices[offset].v0, slices[offset].v1)) {
                    canvasSize = canvasSize - slices[offset].v1;
                    list<RowSegment> temp = it->split(x + slices[offset].v0, slices[offset].v1);
                    it = canvas[j].erase(it);
                    canvas[j].insert(it, temp.begin(), temp.end());
                    filled = true;

                }
            }
            if (!filled) {
                LogError("Can not filled row %d : %d, %d", j, slices[offset].v0 + x, x + slices[offset].v0 + slices[offset].v1);
                for (auto it = canvas[j].begin(); it != canvas[j].end(); it++) {
                    LogError("height: %d, %d -> %d", it->height, it->start, it->start + it->length);
                }
                // lets output the trace info
                poly->printSummary();
                return false;
            }
        } else {
            RowSegment row = RowSegment(j, 0, maxSize);
            list<RowSegment> newList = row.split(x + slices[offset].v0, slices[offset].v1);
            canvasSize = canvasSize + maxSize - slices[offset].v1;
            canvas.push_back(newList);
        }
        cl_uchar *pointer = map.data() + j * maxSize + slices[offset].v0 + x;
        memset(pointer, 1, sizeof(cl_uchar) * slices[offset].v1);
    }
    LogDebug("Canvas size is %d", canvasSize);
    return true;
}

VectorInt2 BrutalPacking::getResult(const cl_int4 *result, const int start, const int end) {
    LogDebug("Reading result from %d to %d", start, end);
    for (int i = start; i < end; i++) {
        if (result[i].s[2] == 1) {
            return VectorInt2(result[i].s[0], result[i].s[1]);
        }
    }
    return VectorInt2(-1, -1);
}

void BrutalPacking::workerThread(const int index, const shared_ptr<ResultInfo>& item){
    bool quit = false;
    _returnValues[index] = true;
    shared_ptr<Poly> poly = nullptr;
    cl_int4 *result = new cl_int4[canvasSize];
    int rotation;
    while(!quit){
        _sychronizeLock.lock();
        if(_rotations.empty()){
            _sychronizeLock.unlock();
            break;
        }else{
            rotation = _rotations.top();
            poly = item->poly->rotate1(rotation);
            _rotations.pop();
            _sychronizeLock.unlock();
        }

        int h = poly->getHeight();
        int w = poly->getWidth();
        VectorInt2 idx(-1, -1);
        _candidate_inputs[index] = clCreateBuffer(_contexts[index], CL_MEM_READ_ONLY, sizeof(cl_uchar) * h * w, NULL, &_cl_errs[index]);
        if (_cl_errs[index] != CL_SUCCESS) {
            printCLError(_cl_errs[index]);
            LogError("Can not create poly data in device %d", index);
            _returnValues[index] = false;
            break;
        }

        _cl_errs[index] = clEnqueueWriteBuffer(_commands[index], _candidate_inputs[index], CL_TRUE, 0, sizeof(cl_uchar) * h * w, poly->getData(), 0, NULL, NULL);
        if (_cl_errs[index] != CL_SUCCESS) {
            printCLError(_cl_errs[index]);
            LogError("Can not write candidate into device %d for device %d", _cl_errs[index], index);
            printCLError(_cl_errs[index]);
            _returnValues[index] = false;
            break;
        }
        _cl_errs[index] = clSetKernelArg(_kernels[index], 0, sizeof(cl_mem), &_map_inputs[index]);

        _cl_errs[index] |= clSetKernelArg(_kernels[index], 1, sizeof(cl_mem), &_canvas_inputs[index]);

        _cl_errs[index] |= clSetKernelArg(_kernels[index], 2, sizeof(cl_mem), &_candidate_inputs[index]);

        _cl_errs[index] |= clSetKernelArg(_kernels[index], 3, sizeof(cl_mem), &_result_outputs[index]);


        _cl_errs[index] |= clSetKernelArg(_kernels[index], 4, sizeof(int), &maxSize);
        _cl_errs[index] |= clSetKernelArg(_kernels[index], 5, sizeof(int), &maxSize);

        _cl_errs[index] |= clSetKernelArg(_kernels[index], 6, sizeof(int), &w);

        _cl_errs[index] |= clSetKernelArg(_kernels[index], 7, sizeof(int), &h);
        _cl_errs[index] |= clSetKernelArg(_kernels[index], 8, sizeof(int), &canvasSize);

        if (_cl_errs[index] != CL_SUCCESS) {
            LogError("Error: Failed to set kernel arguments! %d for device %d\n", _cl_errs[index], index);
            printCLError(_cl_errs[index]);
            _returnValues[index] = false;
            break;
        }


        memset(result, 0, sizeof(cl_int4) * canvasSize);
        size_t step = _loopLimit * _locals[index];

        bool hasError = false;
        for(size_t start = 0, end = 0; start < canvasSize; start = end){
            end = start + step;
            if (end > canvasSize){
                auto reminder = canvasSize - start;
                end = (reminder / _locals[index] + 1) * _locals[index] + start;
            }
            _cl_errs[index] = clEnqueueNDRangeKernel(_commands[index], _kernels[index], 1, &start, &end, &_locals[index], 0, NULL, NULL);
            if(_cl_errs[index] != CL_SUCCESS){
                printCLError(_cl_errs[index]);
                hasError = true;
                break;
            }
            _cl_errs[index] = clFinish(_commands[index]);
            if(_cl_errs[index] != CL_SUCCESS){
                printCLError(_cl_errs[index]);
                hasError = true;
                break;
            }
            _cl_errs[index] = clEnqueueReadBuffer(_commands[index], _result_outputs[index], CL_TRUE, 0, sizeof(cl_int4) * canvasSize, result, 0, NULL, NULL);
            if (_cl_errs[index] != CL_SUCCESS) {
                printCLError(_cl_errs[index]);
                hasError = true;
                break;
            }
            if (end <= canvasSize){
                idx = getResult(result, start, end);
            }else{
                idx = getResult(result, start, canvasSize);
            }

            if (idx.v0 >= 0) {
                LogDebug("Found  position: %d, %d for rotation %d for device %d", idx.v0, idx.v1, rotation * 90, index);
                break;
            }
        }
        if (hasError){
            _returnValues[index] = false;
            break;
        }

        _sychronizeLock.lock();
        if (idx.v0 >= 0) {
            LogDebug("Found canvas position: %d, %d for rotation %d for device %d", idx.v0, idx.v1, rotation * 90, index);
            _targetPositions.emplace_back(idx.v0, idx.v1, rotation, poly->getHeight());

            _polyCache.push_back(poly);
        } else {
            LogDebug("Can not found target within canvas, expand canvas");
            auto canvasHeight = canvas.size();
            if (expandCanvas(poly)) {
                _targetPositions.emplace_back(0, canvasHeight, rotation, poly->getHeight());
                _polyCache.push_back(poly);
            } else {
                _expandResult.push_back(false);
            }
        }
        _sychronizeLock.unlock();

        if (_candidate_inputs[index] != NULL) {
            clReleaseMemObject(_candidate_inputs[index]);
            _candidate_inputs[index] = NULL;
        }
    }

    delete[] result;


}

bool BrutalPacking::insertPloy(const shared_ptr<ResultInfo>& item, const bool rotateType, const bool cpuSimulator) {
    errorCode = ERROR_HARDWARE;

    if (canvasSize == 0) {
        if (!fillCanvas(item->poly, 0, 0)) {
            LogError("Can not fill canvas with %d, %d", 0, 0);
            return false;
        } else {
            item->x = 0;
            item->y = 0;
            item->w = item->poly->getWidth();
            item->h = item->poly->getHeight();
            item->poly = item->poly;
            item->rotation = 0;
            return true;
        }
    }

    // lets create canvas data



    cl_int2 *data = new cl_int2[canvasSize];
    memset(data, 0, sizeof(cl_int2) * canvasSize);
    int offset = 0;
    for (int i = 0; i < canvas.size(); i++ ) {
        for (auto it = canvas[i].begin(); it != canvas[i].end(); it++) {
            cl_int2* source = it->composeData(i);
            memcpy(&data[offset], source, (it->length) * sizeof(cl_int2));
            offset += (it->length);
            delete[] source;
        }
    }
    assert(canvasSize == offset);

    _targetPositions.clear();
    _expandResult.clear();
    _polyCache.clear();
    std::stack<int> tempStack;
    _rotations.swap(tempStack);

    int rotation = 2;
    if(item->poly->getPointSize() != 4){
        rotation = 4;
    }
    for(int i = rotation - 1; i >= 0; i--){
        _rotations.push(i);
    }


    bool returnValue = true;


    for(int i = 0; i < _devicesCount; i++){
        _candidate_inputs[i] = _canvas_inputs[i] = _result_outputs[i] = NULL;
        _canvas_inputs[i] = clCreateBuffer(_contexts[i], CL_MEM_READ_ONLY, sizeof(cl_int2) * canvasSize, NULL, &_cl_errs[i]);
        if (_cl_errs[i] != CL_SUCCESS) {
            LogError("Can not create canvas data in device %d", i);
            returnValue = false;
        }
        _result_outputs[i] = clCreateBuffer(_contexts[i], CL_MEM_WRITE_ONLY, sizeof(cl_int4) * canvasSize, NULL, &_cl_errs[i]);
        if (_cl_errs[i] != CL_SUCCESS) {
            LogError("Can not create result data in device %d", i);
            returnValue = false;
        }

        if(!cpuSimulator){
            _cl_errs[i] = clEnqueueWriteBuffer(_commands[i], _canvas_inputs[i], CL_TRUE, 0, sizeof(cl_int2) * canvasSize, data, 0, NULL, NULL);
            if (_cl_errs[i] != CL_SUCCESS) {
                LogError("Can not write canvas data into device %d", i);
                returnValue = false;
            }
            _cl_errs[i] = clEnqueueWriteBuffer(_commands[i], _map_inputs[i], CL_TRUE, 0, sizeof(cl_uchar) * maxSize * maxSize, map.data(), 0, NULL, NULL);
            if (_cl_errs[i] != CL_SUCCESS) {
                LogError("Can not write map data into device %d", i);
                returnValue = false;
            }
        }
        _workerThreads[i] = new std::thread(&BrutalPacking::workerThread, this, i, item);
        // now lets fire up the computing thread!!! yeah!!

    }

    // now we wait
    for(int i = 0; i < _devicesCount; i++){
        if(_workerThreads[i] != nullptr){
            _workerThreads[i]->join();
            delete _workerThreads[i];
            _workerThreads[i] = nullptr;
            LogDebug("Worker Thread %d finished", i);
        }
        returnValue = (returnValue && _returnValues[i]);
    }
    if (_expandResult.size() == rotation) {
        LogInfo("Can not find available space, its Full!");
        errorCode = ERROR_FULL;
        returnValue = false;
    }
    if (!_targetPositions.empty() && returnValue) {
        int min = maxSize * maxSize;
        int idx = 0;
        for (int i = 0; i < _targetPositions.size(); i++) {
            int temp = _targetPositions[i].v0 + (_targetPositions[i].v1 + _targetPositions[i].v3)* maxSize;
            if (min > temp) {
                min = temp;
                idx = i;
            }
        }

        if (!fillCanvas(_polyCache[idx], _targetPositions[idx].v0, _targetPositions[idx].v1)) {
            LogError("Something wrong when fill canvas with poly data, BUG!!!!!");
            item->x = _targetPositions[idx].v0;
            item->y = _targetPositions[idx].v1;
            item->rotation = _targetPositions[idx].v2 * 90;
            errorCode = ERROR_FILL_CANVAS;
            returnValue = false;
        } else {
            LogDebug("inserted into position %d, %d", _targetPositions[idx].v0, _targetPositions[idx].v1);
            item->x = _targetPositions[idx].v0;
            item->y = _targetPositions[idx].v1;
            item->w = _polyCache[idx]->getWidth();
            item->h = _polyCache[idx]->getHeight();
            item->poly = _polyCache[idx];
            item->rotation = _targetPositions[idx].v2 * 90;
            returnValue = true;
        }

    }

    for(int i = 0; i < _devicesCount;  i++){
        if (_candidate_inputs[i] != NULL) {
            clReleaseMemObject(_candidate_inputs[i]);
            _candidate_inputs[i] = NULL;
        }

        if (_canvas_inputs[i] != NULL) {
            clReleaseMemObject(_canvas_inputs[i]);
            _canvas_inputs[i] = NULL;
        }
        if (_result_outputs[i] != NULL) {
            clReleaseMemObject(_result_outputs[i]);
            _result_outputs[i] = NULL;
        }
        printCLError(_cl_errs[i]);
    }

    delete[] data;

    return returnValue;
}

void BrutalPacking::printCLError(cl_int err) {
    if(err != CL_SUCCESS){
        switch (err) {
            case CL_INVALID_PROGRAM_EXECUTABLE:
                LogError("there is no successfully built program executable available for device associated with command_queue");
                break;
            case CL_INVALID_COMMAND_QUEUE:
                LogError("command_queue is not a valid command-queue");
                break;
            case CL_INVALID_KERNEL:
                LogError("kernel is not a valid kernel object");
                break;
            case CL_INVALID_CONTEXT:
                LogError("context associated with command_queue and kernel is not the same or if the context associated with command_queue and events in event_wait_list are not the same");
                break;
            case CL_INVALID_KERNEL_ARGS:
                LogError("the kernel argument values have not been specified");
                break;
            case CL_INVALID_WORK_DIMENSION:
                LogError("work_dim is not a valid value");
                break;
            case CL_INVALID_WORK_GROUP_SIZE:
                LogError("CL_INVALID_WORK_GROUP_SIZE");
                break;
            case CL_INVALID_WORK_ITEM_SIZE:
                LogError("the number of work-items specified in any of local_work_size[0], ... local_work_size[work_dim - 1] is greater than the corresponding values specified by CL_DEVICE_MAX_WORK_ITEM_SIZES[0], .... CL_DEVICE_MAX_WORK_ITEM_SIZES[work_dim - 1]");
                break;
            case CL_INVALID_GLOBAL_OFFSET:
                LogError("global_work_offset is not NULL");
                break;
            case CL_OUT_OF_RESOURCES:
                LogError("there is a failure to queue the execution instance of kernel on the command-queue because of insufficient resources needed to execute the kernel. For example, the explicitly specified local_work_size causes a failure to execute the kernel because of insufficient resources such as registers or local memory. Another example would be the number of read-only image args used in kernel exceed the CL_DEVICE_MAX_READ_IMAGE_ARGS value for device or the number of write-only image args used in kernel exceed the CL_DEVICE_MAX_WRITE_IMAGE_ARGS value for device or the number of samplers used in kernel exceed CL_DEVICE_MAX_SAMPLERS for device");
                break;
            case CL_MEM_OBJECT_ALLOCATION_FAILURE:
                LogError("there is a failure to allocate memory for data store associated with image or buffer objects specified as arguments to kernel");
                break;
            case CL_INVALID_EVENT_WAIT_LIST:
                LogError("event_wait_list is NULL and num_events_in_wait_list > 0, or event_wait_list is not NULL and num_events_in_wait_list is 0, or if event objects in event_wait_list are not valid events");
                break;
            case CL_OUT_OF_HOST_MEMORY:
                LogError("there is a failure to allocate resources required by the OpenCL implementation on the host");
                break;
            case CL_INVALID_MEM_OBJECT:
                LogError("buffer is not a valid buffer object");
                break;
            case CL_INVALID_VALUE:
                LogError("the region being read or written specified by (offset, cb) is out of bounds or if ptr is a NULL value");
                break;
            case CL_INVALID_PLATFORM: LogError("invalid platform");break;
            case CL_INVALID_DEVICE: LogError("invalid device");break;
            case CL_DEVICE_NOT_FOUND: LogError("no device can be found");break;
            default:
                LogError("Unknow OpenCL Error %d", err);
                //default: LogError("No Error code mapping found");break;
        }
    }

}
Document BrutalPacking::toDebugJson(){
    Document doc;
    doc.SetObject();
    Value w(maxSize);
    Value h(canvas.size());
    doc.AddMember(Value("width", doc.GetAllocator()).Move(), w, doc.GetAllocator());
    doc.AddMember(Value("height", doc.GetAllocator()).Move(), h, doc.GetAllocator());
    Value ret(kArrayType);
    for(int j = std::get<1>(pages[pages.size() - 2 ]); j < std::get<1>(pages[pages.size() - 1]); j++){
        shared_ptr<ResultInfo> temp = results[j];
        Value item(kObjectType);
        Value rotation(temp->rotation);
        item.AddMember(Value(ROTATION, doc.GetAllocator()).Move(), rotation, doc.GetAllocator());


        Value idx(j);
        item.AddMember(Value("index", doc.GetAllocator()).Move(), idx, doc.GetAllocator());

        Value x(temp->x);
        item.AddMember(Value(X, doc.GetAllocator()).Move(), x, doc.GetAllocator());

        Value y(temp->y);
        item.AddMember(Value(Y, doc.GetAllocator()).Move(), y, doc.GetAllocator());

        ret.PushBack(item, doc.GetAllocator());
    }
    Value stop(std::get<1>(pages[pages.size() - 1]));
    doc.AddMember(Value("stop",doc.GetAllocator()).Move(), stop, doc.GetAllocator()),
            doc.AddMember(Value("results", doc.GetAllocator()).Move(), ret, doc.GetAllocator());

    return doc;
}
Document BrutalPacking::toJson(){
    Document doc;
    doc.SetObject();
    Value sheets(kArrayType);
    for(int i = 1; i < pages.size(); i++){
        Value sheet(kObjectType);
        Value sprites(kArrayType);
        Value w(maxSize);
        Value h(std::get<0>(pages[i]));
        sheet.AddMember(Value("width", doc.GetAllocator()).Move(), w, doc.GetAllocator());
        sheet.AddMember(Value("height", doc.GetAllocator()).Move(), h, doc.GetAllocator());

        for(int j = std::get<1>(pages[i-1]); j < std::get<1>(pages[i]); j++){
            shared_ptr<ResultInfo> temp = results[j];
            Value item(kObjectType);

            Value file;
            file.SetString(temp->path.c_str(), temp->path.length(), doc.GetAllocator());
            item.AddMember(Value(FILE_NAME, doc.GetAllocator()).Move(), file, doc.GetAllocator());


            Value area(temp->area);
            item.AddMember(Value(AREA, doc.GetAllocator()).Move(), area, doc.GetAllocator());

            Value rotation(temp->rotation);
            item.AddMember(Value(ROTATION, doc.GetAllocator()).Move(), rotation, doc.GetAllocator());


            Value x(temp->x);
            item.AddMember(Value(X, doc.GetAllocator()).Move(), x, doc.GetAllocator());

            Value y(temp->y);
            item.AddMember(Value(Y, doc.GetAllocator()).Move(), y, doc.GetAllocator());

            Value w(temp->w);
            item.AddMember(Value(W, doc.GetAllocator()).Move(), w, doc.GetAllocator());

            Value h(temp->h);
            item.AddMember(Value(H, doc.GetAllocator()).Move(), h, doc.GetAllocator());


            Value pt1(kArrayType);
            for(auto it = temp->poly->getPoints().begin(); it != temp->poly->getPoints().end(); it++){
                Value v(kArrayType);
                Value x(it->v0);
                Value y(it->v1);
                v.PushBack(x, doc.GetAllocator());
                v.PushBack(y, doc.GetAllocator());
                pt1.PushBack(v, doc.GetAllocator());
            }
            item.AddMember(Value(POINTS, doc.GetAllocator()).Move(), pt1, doc.GetAllocator());

            sprites.PushBack(item, doc.GetAllocator());
        }
        sheet.AddMember(Value("sprites", doc.GetAllocator()).Move(), sprites, doc.GetAllocator());
        sheets.PushBack(sheet, doc.GetAllocator());
    }

    doc.AddMember(Value("sheets", doc.GetAllocator()).Move(), sheets, doc.GetAllocator());

    return doc;
}
int BrutalPacking::startDebugPacking(bool rotationType, const char *str, const std::string& path) {
    if (!deviceInited) {
        LogError("Device has not been inited, quit!");
        return false;
    }
    // well we need to read debug file
    unordered_map<int, VectorInt3> debugList;
    Document doc;
    doc.Parse(str);
    if(doc.HasMember("results")){
        rapidjson::Value &node = doc["results"];
        for(int i = 0; i < node.Size(); i++){
            rapidjson::Value& item = node[i];
            debugList[item["index"].GetInt()] = VectorInt3(item[X].GetInt(), item[Y].GetInt(), item[ROTATION].GetInt()/90);
        }
    }
    int stop = doc["stop"].GetInt();
    for(int i = 0; i < stop; i++){
        auto it = debugList.find(i);
        if(it != debugList.end()){
            shared_ptr<Poly> poly = results[i]->poly->rotate1(it->second.v2);
            if (!fillCanvas(results[i]->poly->rotate1(it->second.v2), it->second.v0,  it->second.v1)) {
                LogError("Can not fill poly number %d -> %d, %d, %d", i, it->second.v0, it->second.v1, it->second.v2);
                return 0;
            }
        }
    }
    if (!insertPloy(results[stop], rotationType, false)) {
        LogError("insert failed");
    }else{
        LogInfo("Debug insert successful");
    }

    // now we can draw stuff
    return 1;
}
int BrutalPacking::startPacking(bool rotationType) {
    if (!deviceInited) {
        LogError("Device has not been inited, quit!");
        return false;
    }
    pages.clear();
    pages.emplace_back(0, 0);
    auto startTime = std::chrono::steady_clock::now();
    for(int i = 0; i < results.size(); i++){
        // ignore too small object
        if(results[i]->area >= 25){
            LogInfo("Processing %d, area: %d, file: %s", i, results[i]->area, results[i]->path.c_str());
            if (!insertPloy(results[i], rotationType, false)) {

                if(errorCode == ERROR_FULL){
                    LogInfo("Page is full, make another page");
                    pages.emplace_back(canvas.size(), i);
                    reset();
                    i--;
                }else if(errorCode == ERROR_FILL_CANVAS){
                    LogError("Something wrong when merging images, QUITING!!!!");
                    // return debug mode
                    pages.emplace_back(canvas.size(), i);
                    return -1;
                }else{
                    return 0;
                }
            }
        }else{
            LogError("#%d area %d, File %s is too small, IGNORED!!!", i, results[i]->area, results[i]->path.c_str());
        }

    }
    auto duration = std::chrono::duration_cast<std::chrono::seconds>(std::chrono::steady_clock::now() - startTime).count();
    auto mins = duration / 60;
    duration = duration % 60;
    LogInfo("Total cost %d Mins %d Seconds to finish merge %d Images", mins, duration, results.size());
    pages.emplace_back(canvas.size(), results.size());
    return 1;
}