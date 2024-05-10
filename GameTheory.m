% Parameters and configurations
NODES = 25;
TIME_INTERVALS = 36;
alpha = 5;
beta = 3;
gamma = 2;
Q_SAEV = 10;
Q_PT = 5;
Q_SB = 3;
delta = 0.001;
M = 27;

% Strategies
T_AEVS = linspace(0, 1, 10);
T_PT = linspace(0, 0.5, 10);
P_unit = linspace(0, 2, 10);
P_ticket = linspace(0, 5, 10);

% Load demand data from Excel file
filename = 'all_traveling_orders.xlsx'; % Update with the actual file path
D = zeros(NODES, NODES, TIME_INTERVALS); % Initialize demand matrix
for t = 1:TIME_INTERVALS
    sheet = num2str(t); % Convert the index to a string to specify the sheet name
    D(:,:,t) = readmatrix(filename, 'Sheet', sheet);
end

% Load distance data from Excel file
filename = 'distance.xlsx'; % Update with the actual file path
d = readmatrix(filename);

% Set the random seed
rng(1);

% Gumbel distribution parameters
mu = 0;
beta = 1;

% Generate uniform random numbers
e_SAEV = rand;
e_PT = rand;
e_SB = rand;

% Transform uniform random variables to Gumbel distributed variables
% Using the inverse transform method: X = mu - beta * log(-log(U))
epsilon_SAEV = mu - beta * log(-log(e_SAEV));
epsilon_PT = mu - beta * log(-log(e_PT));
epsilon_SB = mu - beta * log(-log(e_SB));

% Functions
% function D_AEVS = D_AEVS(t, i, j, p_unit, p_ticket, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, epsilon_SAEV, epsilon_PT, epsilon_SB)
%     exp_SAEV = exp(beta * Q_SAEV - alpha * p_unit * d(i, j) + gamma * log(d(i, j)) + epsilon_SAEV);
%     exp_PT = exp(beta * Q_PT - alpha * p_ticket + epsilon_PT);
%     exp_SB = exp(beta * Q_SB - gamma * log(d(i, j)) + epsilon_SB);
%     D_AEVS = (exp_SAEV / (exp_SAEV + exp_PT + exp_SB)) * D(i,j,t);
% end

function D_AEVS_Matrix = D_AEVS(p_unit, p_ticket, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, epsilon_SAEV, epsilon_PT, epsilon_SB)
    
    % Initialize the 3D matrix to store results
    D_AEVS_Matrix = zeros(NODES, NODES, TIME_INTERVALS);

    % Iterate over all time intervals, origin nodes, and destination nodes
    for t = 1:TIME_INTERVALS
        for i = 1:NODES
            for j = 1:NODES
                if i ~= j  % Assuming no demand from a node to itself
                    exp_SAEV = exp(beta * Q_SAEV - alpha * p_unit * d(i, j) + gamma * log(d(i, j)) + epsilon_SAEV);
                    exp_PT = exp(beta * Q_PT - alpha * p_ticket + epsilon_PT);
                    exp_SB = exp(beta * Q_SB - gamma * log(d(i, j)) + epsilon_SB);

                    % Calculate the probability and multiply by the demand
                    D_AEVS_Matrix(i, j, t) = (exp_SAEV / (exp_SAEV + exp_PT + exp_SB)) * D(i, j, t);
                end
            end
        end
    end
end

function D_PT = D_PT(t, i, j, p_unit, p_ticket, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, epsilon_SAEV, epsilon_PT, epsilon_SB)
    exp_SAEV = exp(beta * Q_SAEV - alpha * p_unit * d(i, j) + gamma * log(d(i, j)) + epsilon_SAEV);
    exp_PT = exp(beta * Q_PT - alpha * p_ticket + epsilon_PT);
    exp_SB = exp(beta * Q_SB - gamma * log(d(i, j)) + epsilon_SB);
    D_PT = (exp_PT / (exp_SAEV + exp_PT + exp_SB)) * D(i,j,t);
end

D_PT_Results = zeros(NODES, NODES, TIME_INTERVALS);

% Nested loops to calculate D_AEVS for each t, i, j
for t = 1:TIME_INTERVALS
    for i = 1:NODES
        for j = 1:NODES
            if i ~= j % Assuming demand between the same node is not considered
                D_PT_Results(i, j, t) = D_PT(t, i, j, p_unit, p_ticket, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, epsilon_SAEV, epsilon_PT, epsilon_SB);
            end
        end
    end
end

D_SB_Results = D - D_PT_Results - D_AEVS_Results;

function U = U_AEVS(t, p_unit, p_ticket, t_AEVS, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, NODES, epsilon_SAEV, epsilon_PT, epsilon_SB)
    U = 0;
    for i = 1:NODES
        for j = 1:NODES
            if j ~= i
                U = U + (p_unit - t_AEVS) * d(i,j) * D_AEVS(t, i, j, p_unit, p_ticket, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, epsilon_SAEV, epsilon_PT, epsilon_SB);
            end
        end
    end
end

function U = U_PT(t, p_unit, p_ticket, t_PT, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, NODES, epsilon_SAEV, epsilon_PT, epsilon_SB)
    U = 0;
    for i = 1:NODES
        for j = 1:NODES
            if j ~= i
                U = U + (p_ticket - t_PT * d(i,j)) * D_PT(t, i, j, p_unit, p_ticket, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, epsilon_SAEV, epsilon_PT, epsilon_SB);
            end
        end
    end
end

% Example execution of the Nash Equilibrium calculation (for specific t, p_unit, p_ticket, t_AEVS, t_PT)
t = 20;
t_AEVS = 0.075;
t_PT = 0.1;
U1 = zeros(10, 10);
U2 = zeros(10, 10);

for a = 1:length(P_unit)
    for b = 1:length(P_ticket)
        U1(a,b) = U_AEVS(t, P_unit(a), P_ticket(b), t_AEVS, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, NODES, epsilon_SAEV, epsilon_PT, epsilon_SB);
        U2(a,b) = U_PT(t, P_unit(a), P_ticket(b), t_PT, D, d, Q_SAEV, Q_PT, Q_SB, alpha, beta, gamma, NODES, epsilon_SAEV, epsilon_PT, epsilon_SB);
    end
end

function equilibria = find_nash_equilibria(U1, U2)
    % Get the dimensions of the strategy payoff matrices
    [m, n] = size(U1);
    equilibria = [];

    % Iterate over Player 1's strategies
    for i = 1:m
        % Iterate over Player 2's strategies
        for j = 1:n
            % Check if i is a best response for Player 1
            best_response_p1 = U1(i, j) == max(U1(:, j));
            % Check if j is a best response for Player 2
            best_response_p2 = U2(i, j) == max(U2(i, :));

            % If both are best responses, add to equilibria list
            if best_response_p1 && best_response_p2
                equilibria = [equilibria; i, j];
            end
        end
    end
end

% Assuming U1 and U2 are already defined as matrices of payoffs
equilibria = find_nash_equilibria(U1, U2);
disp('Nash Equilibria:');
disp(equilibria);
