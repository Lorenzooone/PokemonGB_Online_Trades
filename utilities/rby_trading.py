
    enter_room_states = [[0x01, 0x60, 0xD4, 0xFE], [{0x60, 0x61}, {0xD0, 0xD1, 0xD2, 0xD3, 0xD4}, {0xFE}, {0xFE}]]
    
    def debug_answer_with_same(self):
        self.send_predefined_section(self.rby_enter_room_states)
        next = 1
        while True:
            next = self.swap_byte(next)
            