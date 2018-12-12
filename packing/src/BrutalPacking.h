#ifndef _H_BRUTAL_PACKING_H_H
#define _H_BRUTAL_PACKING_H_H

#include <memory>
#include <vector>
#include <string>
#include "Log.h"
#include "Types.h"
#include <math.h>
#include <list>
#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/cl.h>
#endif
#include <cassert>
#include <thread>
#include <mutex>
#include <stack>
#include "rapidjson/document.h"

using namespace st;
using namespace std;

class BrutalPacking {
protected:
    int _loopLimit;
public:
    class RowSegment {

    public:
        int height;
        int start;
        int length;

        RowSegment(int h, int s, int l) {
            height = h;
            start = s;
            length = l;

        }
        cl_int2* composeData(int height){
            cl_int2* ret = new cl_int2[length];
            for(int i = 0; i < length; i++){
                ret[i].s[0] = start + i;
                ret[i].s[1] = height;
            }
            return ret;

        }
        inline std::list<RowSegment> split(int s, int l) {
            int end = start + length;
            int e = s + l;
            if (start > s || end < e) {
                LogError("split: start:%d, end:%d, input: %d, %d", start, end, s, e);
                assert(false);
            }

            std::list<RowSegment> segs;
            // we skip one pixel segment
            // ** seems we can not skip one pixel segment
            if (start < s) {
                segs.push_back(RowSegment(height, start, s - start));
            };
            if (e < end) {
                segs.push_back(RowSegment(height, e, end - e));
            }
            return segs;
        };

        inline bool isInRange(int s, int l) {
            int end = start + length;
            int e = s + l;
            if (start > s || end < e) {
                return false;
            } else {
                return true;
            }
        }
    };

    class Poly : public std::enable_shared_from_this<Poly> {
    protected:
        int _x;
        int _y;
        int _w;
        int _h;
        int _sum;
        std::vector<VectorInt2> _points;
        std::vector<cl_uchar> _data;
        std::vector<VectorInt2> slices;
//        int _pointSize;
        void init(){
            // first we find the bounding box
            int left = 9999999;
            int right = -1;
            int upper = 9999999;
            int lower = -1;
            std::vector<VectorInt2> drawPoints;
            for(int i = 0; i < _points.size(); i++){
                if(left > _points[i].v0){
                    left = _points[i].v0;
                }
                if(right < _points[i].v0){
                    right = _points[i].v0;
                }
                if(upper > _points[i].v1){
                    upper = _points[i].v1;
                }
                if(lower < _points[i].v1){
                    lower = _points[i].v1;
                }
                drawPoints.emplace_back(VectorInt2(_points[i].v0, _points[i].v1));
            }
            drawPoints.emplace_back(VectorInt2(_points[0].v0, _points[0].v1));
            // we create buffer;
            _x = left;
            _y = upper;
            _w = right - left + 1;
            _h = lower - upper + 1;
            _sum = _w * _h;
            VectorInt2 last_pt(-1, -1);
            _data.resize(_w * _h, 0);
            for(int i = 0; i < drawPoints.size(); i++){
                const int x = drawPoints[i].v0 - _x;
                const int y = drawPoints[i].v1 - _y;
                if(last_pt.v0 >=0 && last_pt.v1 >= 0){
                    if(last_pt.v0 == x){
                        if(last_pt.v1 <= y){
                            for(int idx = last_pt.v1; idx <= y; idx++){
                                _data[idx * _w + x] = 1;
                            }
                        }else{
                            for(int idx = y; idx <= last_pt.v1; idx++){
                                _data[idx * _w + x] = 1;
                            }
                        }

                    }else if(last_pt.v1 == y){
                        if(last_pt.v0 <= x){
                            for(int idx = last_pt.v0; idx <= x; idx++){
                                _data[y * _w + idx] = 1;
                            }
                        }else{
                            for(int idx = x; idx <= last_pt.v0; idx++){
                                _data[y * _w + idx] = 1;
                            }
                        }
                    }else{
                        if(abs(last_pt.v0 - x) <= abs(last_pt.v1 - y)){
                            float ratio = (float)(x - last_pt.v0) / (float)(y - last_pt.v1);
                            if(last_pt.v1 <= y){
                                for(int idx = last_pt.v1; idx <= y; idx++){
                                    float temp = ratio * (idx - last_pt.v1) + last_pt.v0;
                                    assert((int)temp < _w);
                                    assert((int)(temp + 0.5f) < _w);
                                    _data[(int)temp + idx * _w] = 1;
                                    _data[(int)(temp + 0.5f) + idx * _w] = 1;
                                }
                            }else{
                                for(int idx = last_pt.v1; idx >= y ; idx--){
                                    float temp = ratio * (idx - last_pt.v1) + last_pt.v0;
                                    assert((int)temp < _w);
                                    assert((int)(temp + 0.5f) < _w);
                                    _data[(int)temp + idx * _w] = 1;
                                    _data[(int)(temp + 0.5f) + idx * _w] = 1;
                                }
                            }
                        }else{
                            float ratio = (float)(y - last_pt.v1) / (float)(x - last_pt.v0);
                            if(last_pt.v0 <= x){
                                for(int idx = last_pt.v0; idx <= x; idx++){
                                    float temp = ratio * (idx - last_pt.v0) + last_pt.v1;
                                    assert((int)temp < _h);
                                    assert((int)(temp + 0.5f) < _h);
                                    _data[(int)(temp) * _w + idx] = 1;
                                    _data[(int)(temp + 0.5f) * _w + idx] = 1;
                                }
                            }else{
                                for(int idx = last_pt.v0; idx >= x; idx--){
                                    float temp = ratio * (idx - last_pt.v0) + last_pt.v1;
                                    assert((int)temp < _h);
                                    assert((int)(temp + 0.5f) < _h);
                                    _data[(int)(temp) * _w + idx] = 1;
                                    _data[(int)(temp + 0.5f) * _w + idx] = 1;
                                }
                            }
                        }
                    }
                }
                last_pt.v0 = x;
                last_pt.v1 = y;
            }

            for(int y = 0; y < _h; y++){
                int start = -1;
                bool drawed = false;
                int offset = _w * y;
                for(int x = 0; x < _w; x++){
                    if(_data[offset + x] == 1){
                        if(start >= 0){
//                            drawed = true;
                            for(int i = x; i >= start; i--){
                                _data[offset + i] = 1;
                            }
                        }
                        start = x;
                    }
                }

            }
        }



        void computeSlice() {
            slices.clear();
            for(int y = 0; y < _h; y++){
                int left = -1;
                int right  = -1;
                int offset = _w * y;
                for(int x = 0; x < _w; x++){
                    if(_data[offset + x] == 1){
                        if(left < 0 && right < 0){
                            right = left = x;
                        }else if(right < x){
                            right = x;
                        }

                    }
                }
//                LogDebug("Push slice %d -> %d %d",y, left, right);
                assert(right >= left && left >= 0);
                slices.push_back(VectorInt2(left, right - left + 1));

            }

        }
    public:
        inline cl_uchar *getData() {
            return _data.data();
        }
        inline int getDataSize(){
            return _data.size();
        }

        inline int getSum() {
            return _sum;
        }
        inline int getPointSize(){
            return _points.size();
        }

        Poly(const std::vector<VectorInt2>& ps) {
            //data = nullptr;
            _points = ps;
            init();
            computeSlice();
        }


        ~Poly() {

        };

        inline std::shared_ptr<Poly> rotate90(int n) {

            std::vector<VectorInt2> points;
            int minX = 9999999;
            int minY = 9999999;
            if(n == 1){
                for(int i = 0; i < _points.size(); i++){
                    int x =   _points[i].v1;
                    int y =  _points[i].v0;
                    points.push_back(VectorInt2(x, y));
                }
            }else if(n == 2){
                for(int i = 0; i < _points.size(); i++){
                    int x = -_points[i].v0;
                    int y = _points[i].v1;
                    points.push_back(VectorInt2(x, y));
                }
            }else if( n== 3){
                for(int i = 0; i < _points.size(); i++){
                    int x =  -_points[i].v1;
                    int y =  _points[i].v0;
                    points.push_back(VectorInt2(x, y));
                }
            }else{
                return std::make_shared<Poly>(_points);
            }
            for(int i = 0; i < points.size(); i++){
                if(minX > points[i].v0){
                    minX = points[i].v0;
                }
                if(minY > points[i].v1){
                    minY = points[i].v1;
                }
            }
            for(int i = 0; i < points.size(); i++){
                points[i].v0 -= minX;
                points[i].v1 -= minY;
            }
            return std::make_shared<Poly>(points);

        }

        inline const std::vector<VectorInt2>& getSlice() {
            return slices;
        }
        inline int getWidth() {
            return _w;
        }

        inline int getHeight() {
            return _h;
        }

        inline int getArea() {
            return _w * _h;
        }

        inline const std::vector<VectorInt2> &getPoints() {
            return _points;
        }


        inline std::shared_ptr<Poly> rotate1(int n) {
            return rotate90(n);
        }

        inline int getLength(VectorInt2 &lv, VectorInt2 &rv) {
            int diffx = lv.v0 - rv.v0;
            int diffy = lv.v1 - rv.v1;

            float res = sqrt(diffx * diffx + diffy * diffy);
            return ceil(res);
        }
        inline void printSummary(){
            printf("Width %d height %d x %d y %d\n", _w, _h, _x, _y);
            for(int y = 0; y < _h; y++) {
                for (int i = 0; i < _w; i++) {
                    if (_data[_w * y + i] == 1) {
                        printf("*");
                    } else {
                        printf(" ");
                    }
                }
                printf("\n");
            }

            for(int i = 0; i < _points.size(); i++){
                LogDebug("x %d y %d", _points[i].v0, _points[i].v1);
            }

        }
    };

public:
    struct ResultInfo {
        int x;
        int y;
        int w;
        int h;
        int rotation;
        shared_ptr<Poly> poly;

//        shared_ptr<Poly> poly2;


//        int x2;
//        int y2;
//        int w2;
//        int h2;
//        int rotation2;

        int area;
//        int rectArea;

        std::string path;
//        std::string altPath;
//
//        ResultInfo(int x, int y, int w, int h, shared_ptr<Poly> poly, int rotation)
//                : x(x), y(y), w(w), h(h), poly(poly), rotation(rotation) {
//        }
    };

private:
    static const char *POINTS;
    static const char *AREA;
    static const char* ROTATION;
    static const char* X;
    static const char* Y;
    static const char* W;
    static const char* H;
    static const char *FILE_NAME;




    static const bool ERROR_HARDWARE = 1;
    static const bool ERROR_FULL = 0;
    static const bool ERROR_FILL_CANVAS = 2;
public:
    static const bool ROTATION_90 = false;
//    static const bool ROTATION_45 = true;
protected:
    // lock
    std::mutex _sychronizeLock;

    bool deviceInited;

    size_t global;


    cl_uint _devicesCount;
    cl_device_id* _device_ids;             // compute device id

    cl_context* _contexts;                 // compute context

    cl_command_queue* _commands;          // compute command queue

    cl_program* _programs;                 // compute program

    cl_kernel* _kernels;                   // compute kernel


    cl_mem* _canvas_inputs;
    cl_mem* _map_inputs;
    cl_mem* _candidate_inputs;
    cl_mem* _result_outputs;
    size_t* _locals;                       // local domain size for our calculation

    int _cl_errs[10];
    static const char *KernelDetection;
    const int maxSize;
//    const int width;
//    const int height;
    bool _returnValues[10];

    std::vector<shared_ptr<ResultInfo>> results;


    // for thread sychorinze data struture
    vector<VectorInt4> _targetPositions;
    vector<bool> _expandResult;
    vector<shared_ptr<Poly>> _polyCache;
    std::stack<int> _rotations;
    std::thread** _workerThreads;

    int canvasHeight;

    char *intersections;
    //====================
    std::vector<std::list<RowSegment>> canvas;
    int canvasSize;

    //====================
    bool expandCanvas(const shared_ptr<Poly>& poly);

    bool fillCanvas(const shared_ptr<Poly>& poly, const int x, const int y);

    bool insertPloy(const shared_ptr<ResultInfo>& item, const bool rotateType = false, const bool cpuSimulator = false);

    VectorInt2 getResult(const cl_int3 *result, const int start, const int end);

    void printCLError(cl_int err);

    vector<cl_uchar> map;
    inline void reset(){
        memset(map.data(), 0, sizeof(cl_uchar) * maxSize * maxSize);
        std::vector<std::list<RowSegment>> temp;
        canvas.swap(temp);
        canvasSize = 0;
    }
    bool errorCode;

    std::vector<std::tuple<int, int>> pages;



    // CPU MOCK TEST
    // FOR DEBUG AND OTHER PURPOSE ONLY
//    void detection(int idx, u_char* map, cl_int2* canvas, u_char* candidate, cl_int3* result,
//            const int width, const int height, const int w, const int h, const int size);

public:
    BrutalPacking(int size, int loopLimit = 1000);

    ~BrutalPacking();
    rapidjson::Document toJson();
    rapidjson::Document toDebugJson();

    bool initDevice();

    bool readPolygon(const char *str);

    int startPacking(bool rotationType);
    int startDebugPacking(bool rotationType,const char *str, const std::string& path);

    inline std::vector<shared_ptr<ResultInfo>> &getResults() {
        return results;
    }

    inline std::vector<std::list<RowSegment>> &getCanvas() {
        return canvas;
    }

    inline std::vector<cl_uchar> &getMap() {
        return map;
    }

    void workerThread(const int index, const shared_ptr<ResultInfo>& item);
};


#endif