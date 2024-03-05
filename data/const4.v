module const4(
  input wire [3:0] a,
  output wire [4:0] out
);
  assign out = a + 4'b1010;
endmodule
