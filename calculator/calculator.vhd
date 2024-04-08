library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity calculator is
    Port (
        clock   : in std_logic;               -- Clock signal
        b0      : in std_logic;               -- Button 0, Capture input
        b1      : in std_logic;               -- Button 1, Enter
        b2      : in std_logic;               -- Button 2, Action
        op      : in std_logic_vector(1 downto 0);  -- Action switches (2)
        data    : in std_logic_vector(7 downto 0);  -- Input data switches (8)
        digit0  : out std_logic_vector(6 downto 0); -- Output values for 7-segment display
        digit1  : out std_logic_vector(6 downto 0)  -- Output values for 7-segment display
    );
end entity;	


architecture rt1 of calculator is
	
	
-- Component declaration for the RAM (memram)
component memram is
    port (
        address : in std_logic_vector(3 downto 0);
        clock   : in std_logic;
        data    : in std_logic_vector(7 downto 0);
        wren    : in std_logic;
        q       : out std_logic_vector(7 downto 0)
    );
end component;

-- Component declaration for the hex display (hexdisplay)
component hexdisplay is
    port 
    (
        a      : in std_logic_vector(3 downto 0);
        result : out std_logic_vector(6 downto 0)
    );
end component;


    signal RAM_input         : std_logic_vector(7 downto 0);  -- Input to RAM
    signal RAM_we            : std_logic;                     -- RAM write enable signal
    signal RAM_output        : std_logic_vector(7 downto 0);  -- Output from RAM
    signal stack_ptr         : unsigned(3 downto 0);  -- Stack pointer
    signal mbr               : std_logic_vector(7 downto 0);  -- Memory buffer register
    signal state             : std_logic_vector(2 downto 0);  -- State machine state
    signal temp              : std_logic_vector(3 downto 0);  -- Temporary multiplication result
begin
    -- State machine process
    process (clock)
    begin
        if b1 = '0' and b2 = '0' then
            stack_ptr <= (others => '0');
            mbr <= (others => '0');
            RAM_input <= (others => '0');
            RAM_we <= '0';
            state <= "000";
        else
            if rising_edge(clock) then
                case state is
                    when "000" =>
                        -- State "000" - Waiting for button press
                        if b0 = '0' then
                            -- Button 0 pressed
                            mbr <= data;
                            state <= "111";
                        elsif b1 = '0' then
                            -- Button 1 pressed
                            RAM_input <= mbr;
                            RAM_we <= '1';
                            state <= "001";
                        elsif b2 = '0' then
                            if stack_ptr /= "0000" then
                                stack_ptr <= stack_ptr - 1;
                                state <= "100";
                            end if;
                        end if;
                    when "001" =>
                        -- State "001" - Next step in the write process
                        RAM_we <= '0';
                        stack_ptr <= stack_ptr + 1;
                        state <= "111";
                    when "100" =>
                        -- State "100" - Wait for two clock cycles
                        state <= "101";
                    when "101" =>
                        -- State "101" - Wait for two clock cycles
                        state <= "110";
                    when "110" =>
                        -- State "110" - Output is available
                        case op is
                            when "00" =>
                                mbr <= std_logic_vector(unsigned(RAM_output) + unsigned(mbr));
                                state <= "111";
                            when "01" =>
                                mbr <= std_logic_vector(unsigned(RAM_output) - unsigned(mbr));
                                state <= "111";
                            when "10" =>
                                mbr <= std_logic_vector(unsigned(RAM_output(3 downto 0)) * unsigned(mbr(3 downto 0)));
                                
                                state <= "111";
                            when others =>
                                mbr <= std_logic_vector(unsigned(RAM_output) / unsigned(mbr));
                                state <= "111";
                        end case;
                    when others =>
                        -- State "111" - Wait for all buttons to be released
                        if b0 = '1' and b1 = '1' and b2 = '1' then
                            state <= "000";
                        end if;
                end case;
            end if;
        end if;
    end process;

    -- Instantiate the RAM (memram) component
    ram_instance: memram
    port map (
        address => std_logic_vector(stack_ptr),
        clock => clock,
        data => RAM_input,
        wren => RAM_we,
        q => RAM_output
    );

    -- Instantiate two hex displays for digit0 and digit1
    hexdisplay_0 : hexdisplay
    port map (a => mbr(3 downto 0), result => digit0);

    hexdisplay_1 : hexdisplay
    port map (a => mbr(7 downto 4), result => digit1);
end ]
