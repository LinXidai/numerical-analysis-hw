#include <GL/glut.h>

#include <algorithm>
#include <cmath>
#include <fstream>
#include <filesystem>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr int kSlices = 96;

struct ProfilePoint {
    double radius;
    double height;
};

std::vector<ProfilePoint> profile;
double minHeight = 0.0;
double maxHeight = 1.0;
double maxRadius = 1.0;

int windowWidth = 1000;
int windowHeight = 800;
float yaw = 25.0f;
float pitch = 12.0f;
float distance = 19.0f;
float panX = 0.0f;
float panY = 0.0f;
bool lightEnabled = true;
bool wireframe = false;
bool showAxes = false;
bool animate = false;
int lastTime = 0;

bool loadRightCurve(const std::string& filename) {
    std::ifstream input(filename);
    if (!input) {
        std::cerr << "Cannot open profile CSV: " << filename << '\n';
        return false;
    }

    std::vector<ProfilePoint> loaded;
    std::string line;
    if (!std::getline(input, line)) {
        std::cerr << "Profile CSV is empty: " << filename << '\n';
        return false;
    }

    // final_fit_right_curve.csv is t,x,y; final_fit_full_vase.csv is x,y.
    // Use the header to avoid treating t as the radius.
    std::vector<std::string> headers;
    {
        std::stringstream headerStream(line);
        std::string field;
        while (std::getline(headerStream, field, ',')) {
            headers.push_back(field);
        }
    }
    const auto findHeader = [&headers](const std::string& name) {
        return std::find(headers.begin(), headers.end(), name);
    };
    const auto xHeader = findHeader("x");
    const auto yHeader = findHeader("y");
    if (xHeader == headers.end() || yHeader == headers.end()) {
        std::cerr << "Profile CSV must contain x and y columns.\n";
        return false;
    }
    const std::size_t xIndex =
        static_cast<std::size_t>(xHeader - headers.begin());
    const std::size_t yIndex =
        static_cast<std::size_t>(yHeader - headers.begin());

    while (std::getline(input, line)) {
        std::stringstream stream(line);
        std::vector<std::string> fields;
        std::string field;
        while (std::getline(stream, field, ',')) {
            fields.push_back(field);
        }
        if (fields.size() <= std::max(xIndex, yIndex)) {
            continue;
        }

        try {
            const double radius = std::stod(fields[xIndex]);
            const double height = std::stod(fields[yIndex]);
            if (std::isfinite(radius) && std::isfinite(height)) {
                loaded.push_back({std::abs(radius), height});
            }
        } catch (const std::exception&) {
            // Ignore the CSV header and malformed rows.
        }
    }

    if (loaded.size() < 3) {
        std::cerr << "Profile CSV has fewer than three valid points.\n";
        return false;
    }

    profile = std::move(loaded);
    minHeight = std::numeric_limits<double>::max();
    maxHeight = std::numeric_limits<double>::lowest();
    maxRadius = 0.0;
    for (const ProfilePoint& point : profile) {
        minHeight = std::min(minHeight, point.height);
        maxHeight = std::max(maxHeight, point.height);
        maxRadius = std::max(maxRadius, point.radius);
    }

    const double height = std::max(1e-6, maxHeight - minHeight);
    distance = static_cast<float>(std::max(12.0, height * 1.45));
    return true;
}

void setProjection() {
    const double aspect = static_cast<double>(windowWidth) /
                          static_cast<double>(std::max(1, windowHeight));
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(45.0, aspect, 0.05, 200.0);
    glMatrixMode(GL_MODELVIEW);
}

void drawAxes() {
    if (!showAxes) {
        return;
    }

    glDisable(GL_LIGHTING);
    glLineWidth(1.0f);
    glBegin(GL_LINES);
    glColor3f(0.8f, 0.2f, 0.2f);
    glVertex3d(0.0, 0.0, 0.0);
    glVertex3d(maxRadius * 1.5, 0.0, 0.0);
    glColor3f(0.2f, 0.8f, 0.2f);
    glVertex3d(0.0, 0.0, 0.0);
    glVertex3d(0.0, maxRadius * 1.5, 0.0);
    glColor3f(0.2f, 0.4f, 0.9f);
    glVertex3d(0.0, 0.0, 0.0);
    glVertex3d(0.0, 0.0, maxRadius * 1.5);
    glEnd();
    if (lightEnabled) {
        glEnable(GL_LIGHTING);
    }
}

void drawVase() {
    const double verticalCenter = (minHeight + maxHeight) * 0.5;
    glPushMatrix();
    glTranslated(0.0, -verticalCenter, 0.0);
    glRotatef(pitch, 1.0f, 0.0f, 0.0f);
    glRotatef(yaw, 0.0f, 1.0f, 0.0f);

    const GLenum polygonMode = wireframe ? GL_LINE : GL_FILL;
    glPolygonMode(GL_FRONT_AND_BACK, polygonMode);
    glColor3f(0.72f, 0.35f, 0.16f);

    for (std::size_t row = 0; row + 1 < profile.size(); ++row) {
        const ProfilePoint& p0 = profile[row];
        const ProfilePoint& p1 = profile[row + 1];
        glBegin(GL_QUAD_STRIP);
        for (int slice = 0; slice <= kSlices; ++slice) {
            const double angle = 2.0 * kPi * slice / kSlices;
            const double c = std::cos(angle);
            const double s = std::sin(angle);

            const double dr = p1.radius - p0.radius;
            const double dh = p1.height - p0.height;
            const double length = std::max(1e-9, std::hypot(dr, dh));
            const double normalRadius = dh / length;
            const double normalHeight = -dr / length;

            glNormal3d(normalRadius * c, normalHeight, normalRadius * s);
            glVertex3d(p0.radius * c, p0.height, p0.radius * s);
            glVertex3d(p1.radius * c, p1.height, p1.radius * s);
        }
        glEnd();
    }
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    glPopMatrix();
}

void display() {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    setProjection();
    glLoadIdentity();
    gluLookAt(panX, panY, distance, panX, panY, 0.0, 0.0, 1.0, 0.0);

    glTranslatef(0.0f, 0.0f, 0.0f);
    drawAxes();
    drawVase();
    glutSwapBuffers();
}

void reshape(int width, int height) {
    windowWidth = std::max(1, width);
    windowHeight = std::max(1, height);
    glViewport(0, 0, windowWidth, windowHeight);
}

void resetView() {
    yaw = 25.0f;
    pitch = 12.0f;
    distance = static_cast<float>(std::max(12.0, (maxHeight - minHeight) * 1.45));
    panX = 0.0f;
    panY = 0.0f;
}

void keyboard(unsigned char key, int, int) {
    switch (key) {
    case 27:
    case 'q':
    case 'Q':
        std::exit(0);
    case 'r':
    case 'R':
        resetView();
        break;
    case '+':
    case '=':
        distance = std::max(2.0f, distance - 0.8f);
        break;
    case '-':
    case '_':
        distance = std::min(100.0f, distance + 0.8f);
        break;
    case 'w':
    case 'W':
        pitch += 5.0f;
        break;
    case 's':
    case 'S':
        pitch -= 5.0f;
        break;
    case 'a':
    case 'A':
        yaw -= 5.0f;
        break;
    case 'd':
    case 'D':
        yaw += 5.0f;
        break;
    case 'j':
    case 'J':
        panX -= 0.25f;
        break;
    case 'l':
    case 'L':
        panX += 0.25f;
        break;
    case 'i':
    case 'I':
        panY += 0.25f;
        break;
    case 'k':
    case 'K':
        panY -= 0.25f;
        break;
    case 'f':
    case 'F':
        lightEnabled = !lightEnabled;
        if (lightEnabled) {
            glEnable(GL_LIGHTING);
        } else {
            glDisable(GL_LIGHTING);
        }
        break;
    case '1':
        {
            const GLfloat color[] = {1.0f, 0.78f, 0.58f, 1.0f};
            glLightfv(GL_LIGHT0, GL_DIFFUSE, color);
        }
        break;
    case '2':
        {
            const GLfloat color[] = {0.58f, 0.76f, 1.0f, 1.0f};
            glLightfv(GL_LIGHT0, GL_DIFFUSE, color);
        }
        break;
    case '3':
        {
            const GLfloat color[] = {1.0f, 1.0f, 1.0f, 1.0f};
            glLightfv(GL_LIGHT0, GL_DIFFUSE, color);
        }
        break;
    case 't':
    case 'T':
        wireframe = !wireframe;
        break;
    case 'o':
    case 'O':
        showAxes = !showAxes;
        break;
    case ' ':
        animate = !animate;
        break;
    default:
        break;
    }
    glutPostRedisplay();
}

void specialKeyboard(int key, int, int) {
    switch (key) {
    case GLUT_KEY_LEFT:
        yaw -= 5.0f;
        break;
    case GLUT_KEY_RIGHT:
        yaw += 5.0f;
        break;
    case GLUT_KEY_UP:
        pitch += 5.0f;
        break;
    case GLUT_KEY_DOWN:
        pitch -= 5.0f;
        break;
    case GLUT_KEY_PAGE_UP:
        distance = std::max(2.0f, distance - 0.8f);
        break;
    case GLUT_KEY_PAGE_DOWN:
        distance = std::min(100.0f, distance + 0.8f);
        break;
    default:
        break;
    }
    glutPostRedisplay();
}

void idle() {
    if (animate) {
        const int now = glutGet(GLUT_ELAPSED_TIME);
        if (now - lastTime > 16) {
            yaw += 0.35f;
            lastTime = now;
            glutPostRedisplay();
        }
    }
}

void initializeLighting() {
    const GLfloat ambient[] = {0.18f, 0.18f, 0.18f, 1.0f};
    const GLfloat diffuse[] = {1.0f, 0.78f, 0.58f, 1.0f};
    const GLfloat specular[] = {0.8f, 0.8f, 0.8f, 1.0f};
    const GLfloat position[] = {8.0f, 12.0f, 10.0f, 1.0f};
    const GLfloat material[] = {0.72f, 0.35f, 0.16f, 1.0f};

    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient);
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse);
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular);
    glLightfv(GL_LIGHT0, GL_POSITION, position);
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, material);
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 48.0f);
    glEnable(GL_LIGHT0);
    glEnable(GL_LIGHTING);
    glEnable(GL_COLOR_MATERIAL);
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE);
}

void printHelp(const char* executable) {
    std::cout << "Usage: " << executable
              << " [path-to-final_fit_right_curve.csv]\n\n"
              << "Controls:\n"
              << "  Arrow keys       rotate model\n"
              << "  W/A/S/D          rotate model\n"
              << "  +/- or PgUp/PgDn zoom\n"
              << "  I/J/K/L          move camera target\n"
              << "  F                toggle lighting\n"
              << "  1/2/3            warm/cool/white light\n"
              << "  T                toggle wireframe\n"
              << "  O                toggle axes\n"
              << "  Space            toggle auto rotation\n"
              << "  R                reset view\n"
              << "  Q or Esc         quit\n";
}
}  // namespace

int main(int argc, char** argv) {
    std::string filename;
    if (argc > 1) {
        filename = argv[1];
    } else {
        const std::vector<std::string> candidates = {
            "../../fit_output/final_fit_right_curve.csv",
            "../../../fit_output/final_fit_right_curve.csv",
            "../fit_output/final_fit_right_curve.csv",
        };
        for (const std::string& candidate : candidates) {
            if (std::filesystem::exists(candidate)) {
                filename = candidate;
                break;
            }
        }
        if (filename.empty()) {
            filename = candidates.front();
        }
    }
    if (!loadRightCurve(filename)) {
        printHelp(argv[0]);
        return 1;
    }

    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    glutInitWindowSize(windowWidth, windowHeight);
    glutCreateWindow("Final vase reconstruction - OpenGL");
    glClearColor(0.06f, 0.07f, 0.10f, 1.0f);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_NORMALIZE);
    glShadeModel(GL_SMOOTH);
    initializeLighting();

    glutDisplayFunc(display);
    glutReshapeFunc(reshape);
    glutKeyboardFunc(keyboard);
    glutSpecialFunc(specialKeyboard);
    glutIdleFunc(idle);
    lastTime = glutGet(GLUT_ELAPSED_TIME);
    glutMainLoop();
    return 0;
}
