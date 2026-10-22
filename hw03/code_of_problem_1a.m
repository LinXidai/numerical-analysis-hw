M=[1,2,3
    2,3,4
    3,4,6];
x=[0;-7;5];
y=[-0.2;-7.5;5.4];
v=0;
for i = 1:3
    if(v<abs(x(i)-y(i)))
        v=abs(x(i)-y(i));
    end
end
fprintf("v=%.6f\n",v);
x=M*y;
y=[1;-1;2];
v=0;
for i = 1:3
    if(v<abs(x(i)-y(i)))
        v=abs(x(i)-y(i));
    end
end
fprintf("v=%.6f",v);