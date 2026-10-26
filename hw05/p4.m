a = input("input the min: ");
b = input("input the max: ");
c = input("the number of question: ");
switch c
    case 1
        f = @(x) cos(x).^2;
    case 2
        f = @(x) x .* log(x + 1);
    case 3
        f = @(x) sin(x).^2 - 2 .* x*sin(x) + 1;
    case 4
        f = @(x) 1 ./ (x .* log(x));
    otherwise
        error('题号必须是 1、2、3 或 4。');
end
Y=zeros(3,3);
for i=1:3
    m=0;
    h=(b-a)/2^(i-1);
    for j=1:2^(i-1)-1
        m=m+f(a+h*j);
    end
    Y(i,1)=h*(f(a)+f(b)+2*m)/2;
end
for i=2:3
    for j=2:i
        Y(i,j)=Y(i,j-1)+(Y(i,j-1)-Y(i-1,j-1))/(4^(j-1)-1);
    end
end
disp(Y(3,3));
