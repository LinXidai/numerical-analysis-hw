function x=jacobi(A,b)
n=size(A,1);
if size(A,2)~=n
    error('A is not a square matrix');
end
A=A(:,:);
b=b(:);
D=zeros(n,n);
Q=zeros(n,n);
for i=1:n
    D(i,i)=A(i,i);
    if A(i,i)==0
        error('A is singular');
    end
    Q(i,i)=1/A(i,i);
end
P=zeros(n,n);
P=A-D;
x=zeros(n,1);
for i=1:3
    x=-Q*P*x+Q*b;
    fprintf("the %d th iteration\n", i);
    disp(x);
end
end