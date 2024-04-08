LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;

ENTITY calculator_tb IS
END calculator_tb;

ARCHITECTURE behavior OF calculator_tb IS 

    -- Signal declaration
    signal tb_clock : std_logic := '0';
    signal tb_b0    : std_logic := '1'; -- Start with buttons not pressed
    signal tb_b1    : std_logic := '1'; 
    signal tb_b2    : std_logic := '1';
    signal tb_op    : std_logic_vector(1 downto 0) := (others => '0');
    signal tb_data  : std_logic_vector(7 downto 0) := (others => '0'); 
    signal tb_digit0  : std_logic_vector(6 downto 0);
    signal tb_digit1  : std_logic_vector(6 downto 0);

    -- Clock process to generate the clock signal
    CLOCK_PROCESS : process
    begin
        tb_clock <= '0';
        wait for 10 ns;  -- Clock low period
        tb_clock <= '1';
        wait for 10 ns;  -- Clock high period
    end process CLOCK_PROCESS;

    --Instantiate the calculator
    UUT: entity work.calculator
        PORT MAP (
            clock   => tb_clock,
            b0      => tb_b0,
            b1      => tb_b1,
            b2      => tb_b2,
            op      => tb_op,
            data    => tb_data,
            digit0  => tb_digit0,
            digit1  => tb_digit1
        );

BEGIN -- This begins the architecture's concurrent statement part.

    -- Stimulus process
    STIMULUS_PROCESS: process
    begin
        -- Reset the calculator (if needed)
        tb_b0 <= '1';
        tb_b1 <= '1';
        tb_b2 <= '1';
        tb_op <= (others => '0'); -- No operation selected
        wait for 40 ns; -- Wait for reset to take effect, assuming the reset is synchronous with clock

        -- Example operation: Load the number '2' into the mbr
        tb_data <= "00000010"; --2 in binary
        tb_b0 <= '0'; -- Press Capture button
        wait for 20 ns; 
        tb_b0 <= '1'; -- Release Capture button 
        wait for 20 ns;

        tb_b1 <= '0'; -- Press Enter button to push onto stack
        wait for 20 ns; 
        tb_b1 <= '1'; -- Release Enter button
        wait for 20 ns;

        -- Load the number '6' into the mbr
        tb_data <= "00000110"; -- 6 in binary
        tb_b0 <= '0';
        wait for 20 ns;
        tb_b0 <= '1';
        wait for 20 ns;

        tb_b1 <= '0';
        wait for 20 ns;
        tb_b1 <= '1';
        wait for 20 ns;

        -- Load the number '0' into the MBR and execute subtraction (4-0)
        tb_data <= "00000000"; -- 0 in binary
        tb_b0 <= '0';
        wait for 20 ns;
        tb_b0 <= '1';
        wait for 20 ns;

        -- Assume '01' is the op code for subtraction
        tb_op <= "01"; -- Set operation to SUBTRACT
        tb_b2 <= '0'; -- Press Action button to execute SUBTRACT 
        wait for 20 ns;
        tb_b2 <= '1'; -- Release Action button
        wait for 20 ns;

        -- Now that the top of the stack is 4, and MBR is 0, execute subtraction (6-4)
        -- No need to load '6' again as it's already on top of the stack after the previous push
        tb_b2 <= '0'; -- Press Action button to execute SUBTRACT
        wait for 20 ns;
        tb_b2 <= '1'; -- Release Action button
        wait for 20 ns;

        --End simulation
        wait;
    end process STIMULUS_PROCESS;

END behavior;