syms y;
X=[0;0.5;1;2];
Y = [0, y, 3, 2];
n=numel(X);
D = sym(zeros(n, n)); 
D(:,1)=Y';
for j=2:n
    for i=j:n
        D(i,j)=(D(i,j-1)-D(i-1,j-1))/(X(i)-X(i-j+1));
    end
end
x3_coef=D(n,n);
disp(x3_coef);
eqn = ( x3_coef==6);
sol = solve(eqn,y);
fprintf('y = %.6f\n', double(sol));