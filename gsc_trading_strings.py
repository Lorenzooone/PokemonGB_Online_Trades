
class GSCTradingStrings:
    """
    Class which collects all the text used by the program
    and methods connected to that.
    """
    buffered_str = "Buffered"
    synchronous_str = "Synchronous"
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
    unrecognized_character_str = "UNRECOGNIZED CHARACTER: {letter}"
    error_byte_dropped_str = "Error! At least one byte was not properly transfered!"
    warning_byte_dropped_str = "Warning! At least one byte was not properly transfered!"
    byte_transfer_str = "{send_data} - {recv}"
    crtlc_str = 'You pressed Ctrl+C!'
    waiting_transfer_start_str = "Waiting for the transfer to start..."
    buffered_negotiation_str = '\nThe other player wants to do a {other_buffered} trade.\nWould you like to switch to a {other_buffered} trade?'
    buffered_other_negotiation_str = "\nAsking the other player whether they're willing to do a {own_buffered} trade..."
    buffered_chosen_str = "\nDecided to do a {own_buffered} trade."
    yes_no_str = 'Choice (y = Yes, n=No): '
    action_str = "\nInput the action's number: "
    server_str = "Server: "
    port_str = "Port: "
    room_str = "Room (Default = {room}): "
    emulator_host_str = "Emulator's host: "
    emulator_port_str = "Emulator's port: "
    top_level_menu_str = ("\n=============== Top level Menu ===============\n"
                          "1) Start 2-Player trade (Default)\n"
                          "2) Start Pool trade\n"
                          "3) Options"
                          )
    options_menu_str = ("\n=============== General Options ===============\n"
                        "0) Exit (Default)\n"
                        "1) Server for connection: {server_host}\n"
                        "2) Port for connection: {server_port}\n"
                        "3) {sanity_checks_str}\n"
                        "4) Change Verbosity (Current: {verbose})\n"
                        "\n=============== 2-Player trade Options ===============\n"
                        "5) Change to {other_buffered} Trading (Current: {own_buffered})\n"
                        "6) {kill_on_byte_drops_str}"
                        "{emulator_str}"
                        )
    emulator_options_str = ("\n\n=============== Emulator Options ===============\n"
                            "7) Host for emulator connection: {emulator_host}\n"
                            "8) Port for emulator connection: {emulator_port}"
                            )

    def get_buffered_str(buffered):
        if buffered:
            return GSCTradingStrings.buffered_str
        return GSCTradingStrings.synchronous_str
    
    def buffered_negotiation_print(buffered):
        print(GSCTradingStrings.buffered_negotiation_str.format(other_buffered=GSCTradingStrings.get_buffered_str(not buffered)))
        print(GSCTradingStrings.yes_no_str, end = '')
    
    def buffered_other_negotiation_print(buffered):
        print(GSCTradingStrings.buffered_other_negotiation_str.format(own_buffered = GSCTradingStrings.get_buffered_str(buffered)))
    
    def chosen_buffered_print(buffered):
        print(GSCTradingStrings.buffered_chosen_str.format(own_buffered = GSCTradingStrings.get_buffered_str(buffered)))
            
    def top_menu_print():
        print(GSCTradingStrings.top_level_menu_str)
    
    def get_sanity_checks_str(sanity_checks):
        if sanity_checks:
            return GSCTradingStrings.active_sanity_checks_str
        return GSCTradingStrings.inactive_sanity_checks_str
    
    def get_kill_on_byte_drops_str(kill_on_byte_drops):
        if kill_on_byte_drops:
            return GSCTradingStrings.active_kill_on_byte_drops_str
        return GSCTradingStrings.inactive_kill_on_byte_drops_str
    
    def get_emulator_str(options):
        if not options.is_emulator:
            return ""
        return GSCTradingStrings.emulator_options_str.format(emulator_host=options.emulator[0], emulator_port=options.emulator[1])
        
    def options_menu_print(options):
        print(GSCTradingStrings.options_menu_str.format(server_host=options.server[0], server_port=options.server[1],
                                                     sanity_checks_str=GSCTradingStrings.get_sanity_checks_str(options.do_sanity_checks),
                                                     verbose=options.verbose,
                                                     other_buffered=GSCTradingStrings.get_buffered_str(not options.buffered),
                                                     own_buffered=GSCTradingStrings.get_buffered_str(options.buffered),
                                                     kill_on_byte_drops_str=GSCTradingStrings.get_kill_on_byte_drops_str(options.kill_on_byte_drops),
                                                     emulator_str = GSCTradingStrings.get_emulator_str(options)
                                                     )
             )

    def choice_print():
        print(GSCTradingStrings.action_str, end='')
    
    def change_server_print():
        print(GSCTradingStrings.server_str, end='')
    
    def change_port_print():
        print(GSCTradingStrings.port_str, end='')
    
    def change_room_print(room):
        print(GSCTradingStrings.room_str.format(room=room), end='')
    
    def change_emu_server_print():
        print(GSCTradingStrings.emulator_host_str, end='')
    
    def change_emu_port_print():
        print(GSCTradingStrings.emulator_port_str, end='')