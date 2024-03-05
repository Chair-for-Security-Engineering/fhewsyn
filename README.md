# fhewsyn

Netlist repository for the paper _Improved Circuit Synthesis with Amortized Bootstrapping for FHEW-like Schemes_ by Johannes Mono, Kamil Kluczniak, and Tim Güneysu [[1]].

## Netlists

The directory `data/` contains the following netlists:
- addX:       Add two X-bit numbers.
- calculator: Simple 16-bit calculator supporting addition, substraction and multiplication.
- constX:     Add a X-bit constant to a X-bit number.
- image:      Process an 8x8 grayscale image using a Gaussian blur, sharpening, or ricker wavelet.
- relu:       Computes the ReLU of a 16-bit integer.
- sqrt:       Computes the square root of a 16-bit integer.
- strrev:     Reverses an array of characters of up to 8 characters.
- structs:    Computes the sum for a 32-bit integer field in a multi-dimensional array of structs, each dimension is upper bounded by 2.
- sum:        Computes the sum of two 32-bit integers.
- sum3d:      Computes the sum for a three-dimensional array of 8-bit integers with maximum dimensions 2, 3, 2.

## Cite

```
@article{fhewsyn,
  author       = {Johannes Mono and Kamil Kluczniak and Tim G{\"{u}}neysu},
  title        = {Improved Circuit Synthesis with Amortized Bootstrapping for {FHEW}-like Schemes},
  journal      = {{IACR} Cryptol. ePrint Arch.},
  pages        = {1223},
  year         = {2023},
  url          = {https://eprint.iacr.org/2023/1223},
  timestamp    = {Fri, 08 Sep 2023 15:28:09 +0200},
  biburl       = {https://dblp.org/rec/journals/iacr/MonoKG23.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```

[1]: https://eprint.iacr.org/2023/1223
