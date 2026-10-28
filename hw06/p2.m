c=input("input the number of question");
switch c
    case 1 
        f=@(x) exp(x)-x^2+3*x-2;
    case 2 
        f=@(x) x*cos(x)-2*x^2+3*x-1;
end
a=input("the minimum of x");
b=input("the maximum of x");
maxiter=10000;
if f(a)==0 
  fprintf("the answer is %f",a);   
elseif f(b)==0
    fprintf("the answer is %f",b);
end
for i=1:maxiter
    fprintf("Iteration %d, midpoint = %f\n", i, (a+b)/2);
    if f((a+b)/2)*f(a) > 0
        a=(a+b)/2;
    elseif f((a+b)/2)==0
        fprintf("the answer is %f",(a+b)/2);
        break;
    else
        b=(a+b)/2;
    end
    if (b-a)/2 <10^(-5)
        fprintf("the answer is %f",(a+b)/2);
        break;
    end
end


