%%trapezoidal rule
a=0.25;
i=(cos(a)^2+cos(-a)^2)*a;
disp(i)
%%
% simpson's rule
f=@(x) cos(x).^2;
a=0.25;
i=(cos(a)^2+4*cos(0)^2+cos(-a)^2)*a/3;
disp(i)
%%
% trapezoidal rule
a=0;
b=-0.5;
f=@(x) x*log(x+1);
i=(f(a)+f(b))*(a-b)/2;
disp(i)
%%
% simpson's rule
f=@(x) x*log(x+1);  
a=-0.5;
b=0;
i=(f(a)+4*f((a+b)/2)+f(b))*(b-a)/6;
disp(i)
%%
% trapezoidal rule
a=0.75;
b=1.3;
f=@(x) (sin(x)^2)-2*x*sin(x)+1;
i=(f(a)+f(b))*(b-a)/2;
disp(i)
%%
% %simpson's rule
f=@(x) (sin(x)^2)-2*x*sin(x)+1;
a=0.75;
b=1.3;
i=(f(a)+4*f((a+b)/2)+f(b))*(b-a)/6;
disp(i)
%%
%trapezoidal rule
a=exp(1);
b=a+1;
f=@(x) 1/(x*log(x));
i=(f(a)+f(b))*(b-a)/2;
disp(i)
%%
%simpson's rule
f=@(x) 1/(x*log(x));
a=exp(1);
b=a+1;
i=(f(a)+4*f((a+b)/2)+f(b))*(b-a)/6;
disp(i)