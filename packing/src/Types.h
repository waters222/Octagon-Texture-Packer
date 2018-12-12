#ifndef _TYPES_H_
#define _TYPES_H_

#include <memory>


namespace st{
	typedef unsigned char u_char;

    inline int typesRound2Int(float input){
        return (input > 0)? (int)(input + 0.5) : (int)(input - 0.5);
    }
    struct VectorInt4{
        int v0;
        int v1;
        int v2;
        int v3;

        VectorInt4(int v0, int v1, int v2, int v3) : v0(v0), v1(v1), v2(v2), v3(v3) {
        }

        VectorInt4() : v0(0), v1(0), v2(0), v3(0) {
        }
    };

    struct VectorInt3{
        int v0;
        int v1;
        int v2;

        VectorInt3(int v0, int v1, int v2) : v0(v0), v1(v1), v2(v2) {
        }

        VectorInt3() : v0(0), v1(0), v2(0) {
        }
    };

    struct VectorInt2{
        int v0;
        int v1;
        VectorInt2(int v0, int v1):v0(v0),v1(v1)
        {}
        VectorInt2():v0(0),v1(0)
        {}
        inline bool operator==(const VectorInt2& other) const{
            return (v0 == other.v0 && v1 == other.v1)? true : false;
        }

        inline bool operator<(const VectorInt2 &other) const {
            if (v1 < other.v1) {
                return true;
            }else if(v1 > other.v1){
                return false;
            }else if(v0 < other.v0){
                return true;
            }else{
                return false;
            }
        }

        inline bool operator>(const VectorInt2 &other) const {
            if (v1 > other.v1) {
                return true;
            }else if(v1 < other.v1){
                return false;
            }else if(v0 > other.v0){
                return true;
            }else{
                return false;
            }
        }
        /*
        bool operator<=(const VectorInt2& other) const{
            return (this == other || this < other);
        }
        bool operator>=(const VectorInt2& other) const{
            return (this == other || this > other);
        }
        */

        inline VectorInt2 operator+(const VectorInt2 &other) const {
            return VectorInt2(v0 + other.v0, v1 + other.v1);
        }

        inline VectorInt2 operator-(const VectorInt2 &other) const {
            return VectorInt2(v0 - other.v0, v1 - other.v1);
        }

        inline int crossProduct(const VectorInt2 &other) const {
            return v0 * other.v1 - v1 * other.v0;
        }
    };

    struct Vector4{
        float v0;
        float v1;
        float v2;
        float v3;

        Vector4(float v0, float v1, float v2, float v3) : v0(v0), v1(v1), v2(v2), v3(v3) {
        }

        Vector4() : v0(0), v1(0), v2(0), v3(0) {
        }
    };

    struct Vector3{
        float v0;
        float v1;
        float v2;

        Vector3(float v0, float v1, float v2) : v0(v0), v1(v1), v2(v2) {
        }

        Vector3() : v0(0), v1(0), v2(0) {
        }
    };


    struct Vector2{
        float v0;
        float v1;
        Vector2(float v0, float v1):v0(v0),v1(v1)
        {}
        Vector2():v0(0),v1(0)
        {}

        inline Vector2 operator+(const Vector2 &other) const {
            return Vector2(v0 + other.v0, v1 + other.v1);
        }

        inline Vector2 operator-(const Vector2 &other) const {
            return Vector2(v0 - other.v0, v1 - other.v1);
        }

    };
}









#endif
