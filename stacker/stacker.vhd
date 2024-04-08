library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity stacker is
    port(
        clock      : in std_logic;
        data       : in std_logic_vector(3 downto 0);
        b0         : in std_logic; -- Load the value from the switches into the MBR
        b1         : in std_logic; -- Push the value in the MBR onto the stack
        b2         : in std_logic; -- Pop the top value off the stack and place it in MBR
        mbrview    : out std_logic_vector(3 downto 0);
        stackview  : out std_logic_vector(3 downto 0);
        stateview  : out std_logic_vector(2 downto 0)
    );
end stacker;

architecture rtl of stacker is

    -- Unsure of this section, check once I open quartus
    component memram_lab
        port(
            address : in std_logic_vector (3 downto 0);
            clock   : in std_logic := '1';
            data    : in std_logic_vector(3 downto 0);
            wren    : in std_logic;
            q       : out std_logic_vector(3 downto 0)
        );
    end component;

    -- Define internal signals
    signal RAM_input  : std_logic_vector(3 downto 0);
    signal RAM_output : std_logic_vector(3 downto 0);
    signal RAM_we     : std_logic;
    signal stack_ptr  : std_logic_vector(3 downto 0);
    signal mbr        : std_logic_vector(3 downto 0);
    signal state      : std_logic_vector(2 downto 0); -- Assuming 8 states 0 to 7

begin
    -- Process to handle button presses and stack operations
    process(clock)
    begin
        -- Check for reset condition
        if b1 = '0' and b2 = '0' then
            stack_ptr <= (others => '0');
            mbr <= (others => '0');
            RAM_input <= (others => '0');
            RAM_we <= '0';
            state <= "000"; -- Reset state
        elsif rising_edge(clock) then
            case state is
                when "000"=>
                    if b0 = '0' then -- if button 0 is pressed
                        MBR <= data;
                        state <= "111";
                    elsif b1 = '0' then -- if button 1 is pressed
                        RAM_input <= MBR;  -- add MBR to stack
                        RAM_we <= '1';  -- Start the write process
                        state <= "001";
                    -- what happens if stack pointer is 0
                    elsif b2 = '0' then -- if button 2 is pressed
                        if unsigned(stack_ptr) > 0 then 
                            stack_ptr <= std_logic_vector(unsigned(stack_ptr) - 1);
                            state <= "100"; -- Start the read process
                        end if;
                    end if;

                when "001"=>
                    RAM_we <= '0'; -- Complete the write process
                    stack_ptr <= std_logic_vector(unsigned(stack_ptr) + 1);
                    state <= "111";
                
                when "100"=>
                    state <= "101";

                when "101"=>
                    state <= "110";
                
                when "110"=>
                    MBR <= RAM_output;
                    state <= "111";

                when others =>
                    if b0 = '1' and b1 = '1' and b2 = '1' then
                        state <= "000";
                    end if;
            end case;
        end if;
    end process;

    mbrview <= mbr;
    stackview <= stack_ptr;
    stateview <= state;

    -- Instance of RAM
    ram_instance : memram_lab
	 
        port map(
            address => stack_ptr,
            clock   => clock,
            data    => RAM_input,
            wren    => RAM_we,
            q       => RAM_output
        );

end rtl;