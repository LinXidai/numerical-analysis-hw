function x=seidel(A,b)
n=size(A,1);
if size(A,2)~=n
    error('A is not a square matrix');
end
A=A(:,:);
b=b(:);
D=zeros(n,n);
Q=zeros(n,n);
for i=1:n
    if A(i,i)==0
        error('zero diagonal element, cannot use Gauss-Seidel directly');
    end
end
for i=1:n
    for j=i+1:n
        Q(i,j)=A(i,j);
    end
end
D=A-Q;

Maxiter=2000;
TOL=0.001;
x=zeros(n,1);
S=inv_lower(D);%O(1/n^3)<O(2n^3/3)
for i=1:Maxiter
    % [M,~]=max(abs(x(:)));
    x=-S*Q*x+S*b;
    % fprintf("the %d th iteration\n", i);
    % disp(x);
    % [N,~]=max(abs(x(:)));
    if max(abs(b-A*x))<TOL
        fprintf("the %d th iteration\n", i);
        disp(x);
        break;
    end
end
end
function Linv = inv_lower(L)
    n = size(L,1);
    Linv = zeros(n);
    for j = 1:n
        Linv(j,j) = 1 / L(j,j);          
        for i = j+1:n
            s = 0;
            for k = j:i-1
                s = s + L(i,k) * Linv(k,j);
            end
            Linv(i,j) = -s / L(i,i);
        end
    end
end
