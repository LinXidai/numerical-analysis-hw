syms x
f  = exp(2*x)*cos(3*x);
df = diff(f, x, 3);

xs = linspace(0, 0.6, 1000);
vals = double(subs(df, x, xs));   % numeric array
M = max(abs(vals));

disp(df)
fprintf('M = %.6f\n', M);
%%
syms x
f  = x*(x-0.6)*(x-0.3);


xs = linspace(0, 0.6, 1000);
vals = double(subs(f, x, xs));   % numeric array
M = max(abs(vals));

disp(f)
fprintf('M = %.6f\n', M);
%%
syms x
f  = sin(log(x));                 % ln(x) -> log(x)
df = diff(f, x, 3);

xs   = linspace(2, 2.6, 1000);
vals = double(subs(df, x, xs));
M    = max(abs(vals));

disp(df)
fprintf('M = %.6f\n', M);
%%
syms x
f  = (x-2)*(x-2.6)*(x-2.4);


xs = linspace(2, 2.6, 1000);
vals = double(subs(f, x, xs));   % numeric array
M = max(abs(vals));

disp(f)
fprintf('M = %.6f\n', M);