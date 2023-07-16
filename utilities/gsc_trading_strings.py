
class GSCTradingStrings:
    """
    Class which collects all the text used by the program
    and methods connected to that.
    """
    version_str = "Version: {major}.{minor}.{build}"
    buffered_str = "Buffered"
    synchronous_str = "Synchronous"
    send_request = "S"
    get_request = "G"
    set_japanese_str = "Set game as Japanese (Current: International)"
    unset_japanese_str = "Set game as International (Current: Japanese)"
    set_egg_str = "Convert received Pokémon to eggs (Current: Do nothing)"
    unset_egg_str = "Don't convert received Pokémon to eggs (Current: Turn to Eggs)"
    unset_japanese_str = "Set game as International (Current: Japanese)"
    active_sanity_checks_str = "Disable Sanity checks (Current: Enabled)"
    inactive_sanity_checks_str = "Enable Sanity checks (Current: Disabled)"
    active_kill_on_byte_drops_str = "Disable Crash on synchronous byte drop (Current: Enabled)"
    inactive_kill_on_byte_drops_str = "Enable Crash on synchronous byte drop (Current: Disabled)"
    websocket_client_error_str = 'Websocket client error:'
    connection_dropped_str = 'Connection dropped'
    p2p_listening_str = 'Listening on {host}:{port}...'
    p2p_server_str = 'Received connection from {host}:{port}'
    bgb_listening_str = 'Listening for bgb on {host}:{port}...'
    bgb_server_str = 'Received bgb connection from {host}:{port}'
    p2p_client_str = 'Connecting to {host}:{port}...'
    socket_error_str = 'Socket error:'
    index_error_str = "Index error!"
    io_error_str = "I/O error({0}): {1}"
    unknown_error_str = "Unexpected error:"
    unrecognized_character_str = "UNRECOGNIZED CHARACTER: {letter}"
    error_byte_dropped_str = "\nError! At least one byte was not properly transfered!\nIf this happens often, you might want to do a buffered trade instead!"
    warning_byte_dropped_str = "\nWarning! At least one byte was not properly transfered!\nIf this happens often, you might want to do a buffered trade instead!"
    byte_transfer_str = "{send_data} - {recv}"
    crtlc_str = 'You pressed Ctrl+C!'
    waiting_transfer_start_str = "Waiting for the transfer to start..."
    enter_trading_room_str = "\nPlease enter the trading room..."
    entered_trading_room_str = "\nEntered the trading room..."
    sit_table_str = "\nYou can now either sit at the table, or quit the room..."
    buffered_sit_table_str = "Please sit at the table to send to the other player your trading data."
    not_received_buffered_data_str = "\nThe other player has not sent their buffered data yet.\nStarting a trade in order to get your data, so the other player can use it."
    found_buffered_data_str = "\nFound the other player's data.\nStarting the trade and sending your data to them, if they don't have it yet."
    recycle_data_str = "\nReusing the previously received data."
    choice_send_str = "\nSending your choice."
    choice_recv_str = "\nWaiting for the other player's choice..."
    accepted_send_str = "\nSending {accepted_str}."
    accepted_wait_str = "\nWaiting for the answer..."
    success_send_str = "\nSending trade confirmation..."
    success_wait_str = "\nWaiting for trade confirmation..."
    close_str = "\nClosing the trade..."
    close_on_next_str = "\nOne of the players wants to close the trade.\nEnabled auto-closing on the next selection..."
    pool_fail_str = "\nThe Pool currently seems to have no free slots. Please try again later..."
    quit_trade_str = "\nYou should now quit the current trade."
    waiting_synchro_str = "\nWaiting for the other player to be synchronized..."
    arrived_synchro_str = "\nThe other player arrived. Starting party information trading..."
    transfer_to_hardware_str = "\rSection {index}: {completion}"
    restart_trade_str = "\nStarting a new trade."
    incompatible_trade_str = "\nIt looks like the requested trade is not possible.\nYou can't do a synchronous trade with the International version and the Japanese version\nif at least one Pokémon is holding mail.\nEither do a Buffered trade, or remove the mail.\nShutting down..."
    separate_section_str = "\n"
    buffered_negotiation_str = '\nThe other player wants to do a {other_buffered} trade.\nWould you like to switch to a {other_buffered} trade?'
    buffered_other_negotiation_str = "\nAsking the other player whether they're willing to do a {own_buffered} trade..."
    buffered_chosen_str = "\nDecided to do a {own_buffered} trade."
    received_buffered_data_str = "\nReceived the trade data from the other player!\nYou can now start the real trade."
    no_recycle_data_str = "\nBoth players' input is required.\nRestarting the trade from scratch."
    no_move_other_data_str = "\nThe other player's input was not required.\nSkipping receiving their moves data."
    reuse_data_str = "\nReusing the other player's trade data."
    move_other_data_str = "\nThe other player's input was required.\nWaiting for their updated moves data..."
    send_move_other_data_str = "\nSending your updated moves data to the other player."
    no_mail_other_data_str = "\nThe other player's party has no mail.\nSkipping receiving their mail data."
    auto_decline_str = "\nSomething weird was detected with the other player's data.\nAutomatically sending Decline."
    mail_other_data_str = "\nThe other player's party has mail.\nWaiting for them to send it."
    send_mail_other_data_str = "\nSending your mail data to the other player."
    pool_receive_data_str = "\nGetting the Pool's trade offer..."
    pool_recycle_data_str = "\nReusing the previous Pool's trade offer..."
    two_player_trade_str = "2P"
    pool_trade_str = "PT"
    accepted_str = "Accept"
    decline_str = "Decline"
    yes_no_str = 'Choice (y = Yes, n=No): '
    action_str = "\nInput the action's number: "
    server_str = "Server: "
    port_str = "Port: "
    room_str = "Room (Default = {room}): "
    max_level_str = "New Max Level (Current = {max_level}): "
    emulator_host_str = "Emulator's host: "
    emulator_port_str = "Emulator's port: "
    game_selector_menu_str = ("\n=============== Game Selector ===============\n"
                          "1) Red/Blue/Yellow\n"
                          "2) Gold/Silver/Crystal\n"
                          "3) Timecapsule in Gold/Silver/Crystal\n"
                          "4) Special Ruby/Sapphire/Emerald/Fire Red/Leaf Green\n"
                          "m) Multiboot Special Ruby/Sapphire/Emerald/Fire Red/Leaf Green"
                          )
    top_level_menu_str = ("\n=============== Top level Menu ===============\n"
                          "1) Start 2-Player trade (Default)\n"
                          "2) Start Pool trade\n"
                          "3) Options"
                          )
    options_menu_str = ("\n=============== General Options ===============\n"
                        "0) Exit (Default)\n"
                        "1) Server for connection: {server_host}\n"
                        "2) Port for connection: {server_port}\n"
                        "3) {japanese_str}\n"
                        "4) {sanity_checks_str}\n"
                        "5) Change Verbosity (Current: {verbose})\n"
                        "\n=============== 2-Player trade Options ===============\n"
                        "6) Change to {other_buffered} Trading (Current: {own_buffered})\n"
                        "7) {kill_on_byte_drops_str}\n"
                        "\n=============== Pools trade Options ===============\n"
                        "8) Set Max Level (Current: {max_level})"
                        "{gen_2_eggify_str}"
                        "{emulator_str}"
                        )
    gen_2_eggify_str = ("\n9) {egg_str}")
    emulator_options_str = ("\n\n=============== Emulator Options ===============\n"
                            "10) Host for emulator connection: {emulator_host}\n"
                            "11) Port for emulator connection: {emulator_port}"
                            )
    
    def int_to_three_str(integer):
        ret = ""
        if integer < 100:
            ret += " "
        if integer < 10:
            ret += " "
        ret += str(integer)
        return ret
    
    def x_out_of_y_str(x, y):
        return GSCTradingStrings.int_to_three_str(x) + "/" + GSCTradingStrings.int_to_three_str(y)

    def get_accepted_str(is_decline):
        if is_decline:
            return GSCTradingStrings.decline_str
        return GSCTradingStrings.accepted_str

    def get_buffered_str(buffered):
        if buffered:
            return GSCTradingStrings.buffered_str
        return GSCTradingStrings.synchronous_str
    
    def buffered_negotiation_print(buffered):
        print(GSCTradingStrings.buffered_negotiation_str.format(other_buffered=GSCTradingStrings.get_buffered_str(not buffered)))
        print(GSCTradingStrings.yes_no_str, end = '')
    
    def version_print(major, minor, build):
        print(GSCTradingStrings.version_str.format(major=major, minor=minor, build=build))
    
    def buffered_other_negotiation_print(buffered):
        print(GSCTradingStrings.buffered_other_negotiation_str.format(own_buffered = GSCTradingStrings.get_buffered_str(buffered)))
    
    def chosen_buffered_print(buffered):
        print(GSCTradingStrings.buffered_chosen_str.format(own_buffered = GSCTradingStrings.get_buffered_str(buffered)))
        if buffered:
            print(GSCTradingStrings.buffered_sit_table_str)
            
    def game_selector_menu_print():
        print(GSCTradingStrings.game_selector_menu_str)
            
    def top_menu_print():
        print(GSCTradingStrings.top_level_menu_str)
    
    def get_japanese_str(japanese):
        if japanese:
            return GSCTradingStrings.unset_japanese_str
        return GSCTradingStrings.set_japanese_str
    
    def get_sanity_checks_str(sanity_checks):
        if sanity_checks:
            return GSCTradingStrings.active_sanity_checks_str
        return GSCTradingStrings.inactive_sanity_checks_str
    
    def get_kill_on_byte_drops_str(kill_on_byte_drops):
        if kill_on_byte_drops:
            return GSCTradingStrings.active_kill_on_byte_drops_str
        return GSCTradingStrings.inactive_kill_on_byte_drops_str
    
    def get_eggify_str(options):
        if not options.gen == 2:
            return ""
        egg_str = GSCTradingStrings.set_egg_str
        if options.egg:
            egg_str = GSCTradingStrings.unset_egg_str
        return GSCTradingStrings.gen_2_eggify_str.format(egg_str=egg_str)
    
    def get_emulator_str(options):
        if not options.is_emulator:
            return ""
        return GSCTradingStrings.emulator_options_str.format(emulator_host=options.emulator[0], emulator_port=options.emulator[1])
        
    def options_menu_print(options):
        print(GSCTradingStrings.options_menu_str.format(server_host=options.server[0], server_port=options.server[1],
                                                     japanese_str=GSCTradingStrings.get_japanese_str(options.japanese),
                                                     sanity_checks_str=GSCTradingStrings.get_sanity_checks_str(options.do_sanity_checks),
                                                     verbose=options.verbose,
                                                     other_buffered=GSCTradingStrings.get_buffered_str(not options.buffered),
                                                     own_buffered=GSCTradingStrings.get_buffered_str(options.buffered),
                                                     kill_on_byte_drops_str=GSCTradingStrings.get_kill_on_byte_drops_str(options.kill_on_byte_drops),
                                                     emulator_str = GSCTradingStrings.get_emulator_str(options),
                                                     max_level = options.max_level,
                                                     gen_2_eggify_str = GSCTradingStrings.get_eggify_str(options)
                                                     )
             )

    def choice_print():
        print(GSCTradingStrings.action_str, end='')
    
    def change_server_print():
        print(GSCTradingStrings.server_str, end='')
    
    def change_port_print():
        print(GSCTradingStrings.port_str, end='')
    
    def change_max_level_print(max_level):
        print(GSCTradingStrings.max_level_str.format(max_level=max_level), end='')
    
    def change_room_print(room):
        print(GSCTradingStrings.room_str.format(room=room), end='')
    
    def change_emu_server_print():
        print(GSCTradingStrings.emulator_host_str, end='')
    
    def change_emu_port_print():
        print(GSCTradingStrings.emulator_port_str, end='')
