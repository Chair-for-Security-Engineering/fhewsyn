module add3(
  input wire [2:0] a,
  input wire [2:0] b,
  output wire [3:0] out
);
  assign out = a + b;
endmodule
