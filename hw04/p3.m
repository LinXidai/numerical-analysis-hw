syms x;
y=((0.4-0.5)*8-(0.4-0.75)*x)/0.25;
eqn = (y==2.4);
sol = solve(eqn,x);
fprintf('x = %.6f\n', double(sol));