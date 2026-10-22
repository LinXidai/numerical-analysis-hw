function x = gauss(A, b)
% GAUSS  Gaussian elimination with scaled partial pivoting.
n = size(A, 1);
if size(A, 2) ~= n
    error('A is not a square matrix');
end
A = A(:,:);
b = b(:);

% Scale factors s(i) = max_j |A(i,j)|.
s = max(abs(A), [], 2);
if any(s == 0)
    error('A is singular');
end

for k = 1:n-1
    % Scaled partial pivoting: choose the row with the largest |A(i,k)|/s(i).
    ratios = abs(A(k:n, k)) ./ s(k:n);
    [~, idx] = max(ratios);
    p = k + idx - 1;

    if A(p, k) == 0
        error('A is singular');
    end

    if p ~= k
        A([k p], :) = A([p k], :);
        b([k p])    = b([p k]);
        s([k p])    = s([p k]);
    end

    for i = k+1:n
        m = A(i, k) / A(k, k);
        A(i, k:n) = A(i, k:n) - m * A(k, k:n);
        b(i)      = b(i)      - m * b(k);
        A(i, k)   = 0;
    end
end

if A(n, n) == 0
    error('A is singular');
end

x = zeros(n, 1);
x(n) = b(n) / A(n, n);
for i = n-1:-1:1
    x(i) = (b(i) - A(i, i+1:n) * x(i+1:n)) / A(i, i);
end
end
