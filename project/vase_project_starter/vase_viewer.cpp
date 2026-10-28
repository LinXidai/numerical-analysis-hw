// OpenGL + FreeGLUT 读取完整花瓶轮廓 CSV 并显示
// CSV 格式：第一行 x,y；后续每行为浮点坐标
// 编译环境需安装 FreeGLUT，并链接 opengl32.lib、glu32.lib、freeglut.lib。
#include <GL/freeglut.h>
#include <fstream>
#include <sstream>
#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>

struct Point { double x, y; };
std::vector<Point> points;
double xmin=0, xmax=0, ymin=0, ymax=0;
int winW=900, winH=900;

bool loadCSV(const std::string& filename) {
    std::ifstream fin(filename);
    if (!fin) {
        std::cerr << "Cannot open " << filename << "\n";
        return false;
    }
    std::string line;
    std::getline(fin, line); // skip header
    while (std::getline(fin, line)) {
        std::stringstream ss(line);
        std::string sx, sy;
        if (!std::getline(ss, sx, ',')) continue;
        if (!std::getline(ss, sy, ',')) continue;
        try {
            points.push_back({std::stod(sx), std::stod(sy)});
        } catch (...) {}
    }
    if (points.size() < 2) return false;
    xmin=xmax=points[0].x; ymin=ymax=points[0].y;
    for (const auto& p : points) {
        xmin=std::min(xmin,p.x); xmax=std::max(xmax,p.x);
        ymin=std::min(ymin,p.y); ymax=std::max(ymax,p.y);
    }
    return true;
}

void display() {
    glClear(GL_COLOR_BUFFER_BIT);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();

    double dx = std::max(1e-6, xmax-xmin);
    double dy = std::max(1e-6, ymax-ymin);
    double cx=(xmin+xmax)/2.0, cy=(ymin+ymax)/2.0;
    double margin=0.12;
    double aspect=(double)winW/(double)winH;
    double halfH=0.5*dy*(1.0+margin);
    double halfW=0.5*dx*(1.0+margin);
    if (halfW/halfH < aspect) halfW=halfH*aspect;
    else halfH=halfW/aspect;
    gluOrtho2D(cx-halfW,cx+halfW,cy-halfH,cy+halfH);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    // coordinate axes
    glColor3f(0.75f,0.75f,0.75f);
    glLineWidth(1.0f);
    glBegin(GL_LINES);
    glVertex2d(cx-halfW,0); glVertex2d(cx+halfW,0);
    glVertex2d(0,cy-halfH); glVertex2d(0,cy+halfH);
    glEnd();

    // complete outline
    glColor3f(0.05f,0.25f,0.75f);
    glLineWidth(2.0f);
    glBegin(GL_LINE_STRIP);
    for (const auto& p : points) glVertex2d(p.x,p.y);
    glEnd();

    // display the symmetry axis
    glColor3f(0.85f,0.25f,0.20f);
    glLineWidth(1.0f);
    glBegin(GL_LINES);
    glVertex2d(0,cy-halfH); glVertex2d(0,cy+halfH);
    glEnd();

    glutSwapBuffers();
}

void reshape(int w, int h) {
    winW=std::max(1,w); winH=std::max(1,h);
    glViewport(0,0,winW,winH);
    glutPostRedisplay();
}

int main(int argc, char** argv) {
    std::string csv = (argc >= 2) ? argv[1] : "cubic_spline_full_vase.csv";
    if (!loadCSV(csv)) {
        std::cerr << "CSV invalid or empty. Run fit_methods.py first and place the output CSV here.\n";
        return 1;
    }
    std::cout << "Loaded " << points.size() << " points from " << csv << "\n";
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB);
    glutInitWindowSize(winW, winH);
    glutCreateWindow("Vase contour - OpenGL + C++");
    glClearColor(1.0f,1.0f,1.0f,1.0f);
    glutDisplayFunc(display);
    glutReshapeFunc(reshape);
    glutMainLoop();
    return 0;
}
