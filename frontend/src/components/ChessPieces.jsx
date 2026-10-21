import React from 'react';

// Standard high-quality vector chess piece paths
export const PieceIcon = ({ piece, className = "w-full h-full" }) => {
  if (!piece) return null;

  const isWhite = piece === piece.toUpperCase();
  const type = piece.toLowerCase();

  const whiteFill = "#ffffff";
  const whiteStroke = "#262626";
  const blackFill = "#262626";
  const blackStroke = "#ffffff";

  // Pawns
  if (type === 'p') {
    return (
      <svg viewBox="0 0 45 45" className={className}>
        <path
          d="m 22.5,9 c -2.21,0 -4,1.79 -4,4 0,0.89 0.29,1.71 0.78,2.38 C 17.33,16.5 16,18.59 16,21 c 0,2.03 0.94,3.84 2.41,5.03 C 15.41,27.09 11,31.58 11,39.5 l 23,0 c 0,-7.92 -4.41,-12.41 -7.41,-13.47 1.47,-1.19 2.41,-3 2.41,-5.03 0,-2.41 -1.33,-4.5 -3.28,-5.62 0.49,-0.67 0.78,-1.49 0.78,-2.38 0,-2.21 -1.79,-4 -4,-4 z"
          fill={isWhite ? whiteFill : blackFill}
          stroke={isWhite ? whiteStroke : blackStroke}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  // Knights
  if (type === 'n') {
    return (
      <svg viewBox="0 0 45 45" className={className}>
        <g
          fill={isWhite ? whiteFill : blackFill}
          stroke={isWhite ? whiteStroke : blackStroke}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M 22,10 C 32.5,11 38.5,18 38,39 L 15,39 C 15,30 25,32.5 23,18" />
          <path d="M 24,18 C 24.38,20.91 18.45,25.37 16,27 C 13,29 13.18,31.34 11,31 C 9.958,30.06 12.41,27.96 11,28 C 10,28 11.19,29.23 10,30 C 9,30 5.997,31 6,26 C 6,24 12,14 12,14 C 12,14 13.89,12.1 14,10.5 C 13.27,7.4 17.2,5 20,5 C 22,5 23.5,6.5 24,8.5" />
          <circle cx="15" cy="14" r="1.5" fill={isWhite ? blackFill : whiteFill} />
        </g>
      </svg>
    );
  }

  // Bishops
  if (type === 'b') {
    return (
      <svg viewBox="0 0 45 45" className={className}>
        <g
          fill={isWhite ? whiteFill : blackFill}
          stroke={isWhite ? whiteStroke : blackStroke}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M 9,36 C 12.39,35.03 19.11,36.43 22.5,34 C 25.89,36.43 32.61,35.03 36,36 C 36,36 37.65,36.54 39,38 C 38.32,38.97 37.35,38.99 36,38.5 C 32.61,37.53 25.89,38.96 22.5,37.5 C 19.11,38.96 12.39,37.53 9,38.5 C 7.646,38.99 6.677,38.97 6,38 C 7.354,36.54 9,36 9,36 z" />
          <path d="M 15,32 C 17.5,34.5 27.5,34.5 30,32 C 30.5,30.5 30,30 30,30 C 30,27.5 27.5,26 27.5,26 C 33,24.5 33.5,14.5 22.5,10.5 C 11.5,14.5 12,24.5 17.5,26 C 17.5,26 15,27.5 15,30 C 15,30 14.5,30.5 15,32 z" />
          <path d="M 25 8 A 2.5 2.5 0 1 1 20 8 A 2.5 2.5 0 1 1 25 8 z" />
          <path d="M 17.5,26 L 27.5,26" stroke={isWhite ? blackFill : whiteFill} />
          <path d="M 22.5,20 L 22.5,26" stroke={isWhite ? blackFill : whiteFill} />
        </g>
      </svg>
    );
  }

  // Rooks
  if (type === 'r') {
    return (
      <svg viewBox="0 0 45 45" className={className}>
        <g
          fill={isWhite ? whiteFill : blackFill}
          stroke={isWhite ? whiteStroke : blackStroke}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M 9,39 L 36,39 L 36,36 L 9,36 z" />
          <path d="M 12,36 L 12,32 L 33,32 L 33,36 z" />
          <path d="M 11,14 L 11,9 L 15,9 L 15,11 L 20,11 L 20,9 L 25,9 L 25,11 L 30,11 L 30,9 L 34,9 L 34,14" />
          <path d="M 12,32 L 14,14 L 31,14 L 33,32 z" />
        </g>
      </svg>
    );
  }

  // Queens
  if (type === 'q') {
    return (
      <svg viewBox="0 0 45 45" className={className}>
        <g
          fill={isWhite ? whiteFill : blackFill}
          stroke={isWhite ? whiteStroke : blackStroke}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M 8.5,14 A 1.5,1.5 0 1,1 5.5,14 A 1.5,1.5 0 1,1 8.5,14 z" />
          <path d="M 17.5,11 A 1.5,1.5 0 1,1 14.5,11 A 1.5,1.5 0 1,1 17.5,11 z" />
          <path d="M 24,10 A 1.5,1.5 0 1,1 21,10 A 1.5,1.5 0 1,1 24,10 z" />
          <path d="M 30.5,11 A 1.5,1.5 0 1,1 27.5,11 A 1.5,1.5 0 1,1 30.5,11 z" />
          <path d="M 39.5,14 A 1.5,1.5 0 1,1 36.5,14 A 1.5,1.5 0 1,1 39.5,14 z" />
          <path d="M 9,26 C 17.5,34.5 27.5,34.5 36,26 C 38.5,14.5 32.5,14 32.5,14 L 28.5,22 L 22.5,13 L 16.5,22 L 12.5,14 C 12.5,14 6.5,14.5 9,26 z" />
          <path d="M 9,31 C 10.5,34.5 34.5,34.5 36,31" />
          <path d="M 11,36 C 11.5,38.5 33.5,38.5 34,36" />
        </g>
      </svg>
    );
  }

  // Kings
  if (type === 'k') {
    return (
      <svg viewBox="0 0 45 45" className={className}>
        <g
          fill={isWhite ? whiteFill : blackFill}
          stroke={isWhite ? whiteStroke : blackStroke}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M 22.5,11.63 L 22.5,6" />
          <path d="M 20,8 L 25,8" />
          <path d="M 22.5,25 C 22.5,25 27,17.5 25.5,14.5 C 24,11.5 21,11.5 19.5,14.5 C 18,17.5 22.5,25 22.5,25" />
          <path d="M 11.5,37 C 17,40.5 28,40.5 33.5,37 C 36.5,30 36.5,22 36.5,22 C 34.5,19 31,19 28.5,21.5 C 26,24 23.5,24 22.5,23 C 21.5,24 19,24 16.5,21.5 C 14,19 10.5,19 8.5,22 C 8.5,22 8.5,30 11.5,37 z" />
          <path d="M 11.5,30 C 17,27 28,27 33.5,30" />
          <path d="M 11.5,33.5 C 17,30.5 28,30.5 33.5,33.5" />
        </g>
      </svg>
    );
  }

  return null;
};
