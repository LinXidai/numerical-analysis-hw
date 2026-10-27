h=input("input the step");
n=input("the number of question");
t=input("range of function");
y=input("initial y");
switch n
    case 1
        f = @(x,y) y./x - (y./x).^2;
    case 2
        f = @(x,y) 1 + (y./x) + (y./x).^2;
    otherwise
        error('题号必须是 1 或 2。');
end
x=1;
fprintf("x=%f  y=%f\n",x,y);
for i=0:(t-1)/h-1
    y=y+h*f(x,y);
    x=x+h; 
    fprintf("x=%f  y=%f\n",x,y);
end
