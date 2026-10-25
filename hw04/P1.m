syms x
f  = exp(2*x)*cos(3*x);
df = diff(f, x, 3);

xs = linspace(0, 2, 1000);
vals = double(subs(df, x, xs));   % numeric array
M = max(abs(vals));

disp(df)
fprintf('M = %.6f\n', M);
%%
syms x
f  = x*(x-0.6)*(x-2);
df = diff(f, x, 3);

xs = linspace(0, 2, 1000);
vals = double(subs(df, x, xs));   % numeric array
M = max(abs(vals));

disp(df)
fprintf('M = %.6f\n', M);