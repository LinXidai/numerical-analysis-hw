#include <stdio.h>
#include <math.h>

#define PI 3.141592653589793
#define E 2.71828
//below are newton's method
/*
#define f(x) (2.0 * sin(PI * (x)) + (x))
#define f1(x) (2.0 * PI * cos(PI * (x)) + 1.0)
#define g(x) (3.0 * pow((x), 2) - pow(E, (x)))
#define g1(x) (6.0 * (x) - pow(E, (x)))

int main(void)
{
    double x = 1.0;
    double p;

    fprintf(stdout, "the first question\n");
    fprintf(stdout,"the 0 iteration, p=1.000000\n");
    for (int i = 1;; i++) {
        p = x - f(x) / f1(x);
        fprintf(stdout, "the %d iteration,p=%f\n", i, p);

        if (fabs(p - x) < 0.01) {
            x = p;
            break;
        }
        x = p;
    }

    fprintf(stdout, "the second question\n");
    fprintf(stdout, "use p0=0\n");
    x = 0.0;
    for (int i = 0;; i++) {
        p = x - g(x) / g1(x);
        fprintf(stdout, "the %d iteration,p=%f\n", i, p);

        if (fabs(p - x) < 0.01) {
            break;
        }
        x = p;
    }
    fprintf(stdout,"use p0=3\n");
     x = 3.0;
    for (int i = 0;; i++) {
        p = x - g(x) / g1(x);
        fprintf(stdout, "the %d iteration,p=%f\n", i, p);

        if (fabs(p - x) < 0.01) {
            break;
        }
        x = p;
    }
    return 0;
}
    */
   #define f(x) (1.0 - (1.0 / PI) * asin((x) / 2.0))
   #define g(x) (pow(E,(x)/2)/(sqrt(3)))
   #define h(x) (log(3.0 * (x) * (x)))
   int main(void){
    double p=1;
    double q=100;
    int i;
    fprintf(stdout,"the first question\n");
    for(i=0;fabs(p-q)>0.01;i++){
        fprintf(stdout,"the %d iteration,p=%f\n",i,p);
        q=p;
        p=f(p);
    }
    fprintf(stdout,"the %d iteration,p=%f\n",i,p);
    fprintf(stdout,"the second question\n");
    fprintf(stdout,"choose p0=0\n");
    p=0;
    q=100;
    for(i=0;fabs(q-p)>0.01;i++){
         fprintf(stdout,"the %d iteration,p=%f\n",i,p);
        q=p;
        p=g(p);
    }
    fprintf(stdout,"the %d iteration,p=%f\n",i,p);
    fprintf(stdout,"choose p0=3.5\n");
    p=3.5;
    q=100;
    for(i=0;fabs(q-p)>0.01;i++){
         fprintf(stdout,"the %d iteration,p=%f\n",i,p);
        q=p;
        p=h(p);
    }
    fprintf(stdout,"the %d iteration,p=%f\n",i,p);  
   }