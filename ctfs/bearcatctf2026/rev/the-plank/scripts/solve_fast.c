/*
 * Fast CTF solver for the plank challenge.
 * Uses bit-slicing with DFS over null space combinations.
 *
 * Build: gcc -O2 -o solve_fast solve_fast.c
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>

#define N 32
#define NSTEPS 100

static const uint8_t target[N] = {
    0x63, 0xc9, 0xa2, 0x2b, 0xcf, 0xef, 0xd4, 0x2b,
    0xeb, 0x83, 0x77, 0x26, 0xe7, 0xfd, 0x09, 0xde,
    0xf3, 0xe5, 0xde, 0x4f, 0x13, 0x0b, 0x6c, 0xb7,
    0x1b, 0xab, 0x0f, 0x8a, 0x13, 0xc5, 0xfd, 0x92
};

/* Forward transformation */
void forward(const uint8_t *flag, uint8_t *out) {
    uint8_t state[N];
    memcpy(state, flag, N);
    for (int j = 0; j < NSTEPS; j++) {
        int y = 140*j + 133;
        int op = (2*j) % 5;
        uint8_t tmp[N];
        if (op == 0) {
            int s = y % N;
            for (int i = 0; i < N; i++)
                tmp[i] = state[i] ^ state[(i+s)%N];
            memcpy(state, tmp, N);
        } else if (op == 1) {
            for (int i = 0; i < N; i++)
                tmp[i] = state[(i+y)%N];
            memcpy(state, tmp, N);
        } else if (op == 2) {
            uint8_t c = y & 0xFF;
            for (int i = 0; i < N; i++)
                state[i] ^= c;
        } else if (op == 3) {
            uint8_t c = y % 256;
            for (int i = 0; i < N; i++)
                state[i] = (uint8_t)(state[i] * c);
        } else if (op == 4) {
            uint8_t c = y % 256;
            for (int i = 0; i < N; i++)
                state[i] = (uint8_t)(state[i] + c);
        }
    }
    memcpy(out, state, N);
}

/* GF(2) matrix-vector multiply: A is n rows, each row is a bitmask */
uint32_t mat_vec(const uint32_t *A, uint32_t v) {
    uint32_t r = 0;
    for (int i = 0; i < N; i++) {
        if (__builtin_popcount(A[i] & v) & 1)
            r |= (1u << i);
    }
    return r;
}

/* GF(2) matrix multiply */
void mat_mul(const uint32_t *A, const uint32_t *B, uint32_t *R) {
    uint32_t BT[N] = {0};
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            if (B[i] & (1u<<j)) BT[j] |= (1u<<i);
    for (int i = 0; i < N; i++) {
        R[i] = 0;
        for (int j = 0; j < N; j++)
            if (__builtin_popcount(A[i] & BT[j]) & 1)
                R[i] |= (1u<<j);
    }
}

/* Known positions and values */
#define NUM_KNOWN 7
static const int known_pos[NUM_KNOWN] = {0, 1, 2, 3, 4, 5, 31};
static const uint8_t known_val[NUM_KNOWN] = {'B', 'C', 'C', 'T', 'F', '{', '}'};
#define NUM_UNK 25
static int unk_pos[NUM_UNK];

/* Precomputed A matrix */
static uint32_t A_mat[N];

/* Build A matrix (same for all bit planes) */
void build_A(void) {
    /* Start with identity */
    for (int i = 0; i < N; i++) A_mat[i] = (1u << i);

    for (int j = 0; j < NSTEPS; j++) {
        int y = 140*j + 133;
        int op = (2*j) % 5;
        if (op == 0) {
            int s = y % N;
            uint32_t Aj[N];
            for (int i = 0; i < N; i++)
                Aj[i] = (1u<<i) | (1u<<((i+s)%N));
            uint32_t tmp[N];
            mat_mul(Aj, A_mat, tmp);
            memcpy(A_mat, tmp, sizeof(A_mat));
        } else if (op == 1) {
            int r = y;
            uint32_t Aj[N];
            for (int i = 0; i < N; i++)
                Aj[i] = 1u << ((i+r)%N);
            uint32_t tmp[N];
            mat_mul(Aj, A_mat, tmp);
            memcpy(A_mat, tmp, sizeof(A_mat));
        }
    }
}

/* Forward partial: compute state at bits 0..k-1 at each step */
void forward_partial(const uint8_t *flag, int mask, uint8_t history[NSTEPS+1][N]) {
    uint8_t state[N];
    for (int i = 0; i < N; i++) state[i] = flag[i] & mask;
    memcpy(history[0], state, N);

    for (int j = 0; j < NSTEPS; j++) {
        int y = 140*j + 133;
        int op = (2*j) % 5;
        uint8_t tmp[N];
        if (op == 0) {
            int s = y % N;
            for (int i = 0; i < N; i++)
                tmp[i] = (state[i] ^ state[(i+s)%N]) & mask;
            memcpy(state, tmp, N);
        } else if (op == 1) {
            for (int i = 0; i < N; i++)
                tmp[i] = state[(i+y)%N];
            memcpy(state, tmp, N);
        } else if (op == 2) {
            uint8_t c = y & mask;
            for (int i = 0; i < N; i++)
                state[i] = (state[i] ^ c) & mask;
        } else if (op == 3) {
            uint8_t c = y % 256;
            for (int i = 0; i < N; i++)
                state[i] = ((uint16_t)state[i] * c) & mask;
        } else if (op == 4) {
            uint8_t c = y % 256;
            for (int i = 0; i < N; i++)
                state[i] = ((uint16_t)state[i] + c) & mask;
        }
        memcpy(history[j+1], state, N);
    }
}

/* Compute constant vector b for bit plane k */
uint32_t compute_b(int k, const uint8_t *flag) {
    int mask = (1 << k) - 1;
    uint8_t history[NSTEPS+1][N];
    if (k > 0)
        forward_partial(flag, mask, history);
    else
        memset(history, 0, sizeof(history));

    uint32_t b = 0;
    for (int j = 0; j < NSTEPS; j++) {
        int y = 140*j + 133;
        int op = (2*j) % 5;
        if (op == 0) {
            int s = y % N;
            uint32_t Aj[N];
            for (int i = 0; i < N; i++)
                Aj[i] = (1u<<i) | (1u<<((i+s)%N));
            b = mat_vec(Aj, b);
        } else if (op == 1) {
            int r = y;
            uint32_t Aj[N];
            for (int i = 0; i < N; i++)
                Aj[i] = 1u << ((i+r)%N);
            b = mat_vec(Aj, b);
        } else if (op == 2) {
            int y_low = y & 0xFF;
            if ((y_low >> k) & 1)
                b ^= 0xFFFFFFFFu;
        } else if (op == 3) {
            int y_mul = y % 256;
            uint32_t bj = 0;
            if (k > 0) {
                for (int i = 0; i < N; i++) {
                    int val = history[j][i] * y_mul;
                    bj |= (((val >> k) & 1) << i);
                }
            }
            b ^= bj;
        } else if (op == 4) {
            int y_add = y % 256;
            int add_k = (y_add >> k) & 1;
            uint32_t bj = 0;
            if (k > 0) {
                int y_add_low = y_add & mask;
                for (int i = 0; i < N; i++) {
                    int carry = ((history[j][i] + y_add_low) >> k) & 1;
                    bj |= ((add_k ^ carry) << i);
                }
            } else {
                if (add_k) bj = 0xFFFFFFFFu;
            }
            b ^= bj;
        }
    }
    return b;
}

/* Solve GF(2) system. Returns number of free variables, fills particular[] and null_vecs[][] */
int solve_gf2(uint32_t rhs, int particular[NUM_UNK], int null_vecs[13][NUM_UNK]) {
    /* Build submatrix for unknown columns */
    uint32_t mat[N];
    int rhs_bits[N];

    for (int row = 0; row < N; row++) {
        uint32_t r = 0;
        for (int idx = 0; idx < NUM_UNK; idx++) {
            if (A_mat[row] & (1u << unk_pos[idx]))
                r |= (1u << idx);
        }
        mat[row] = r;
        rhs_bits[row] = (rhs >> row) & 1;
    }

    /* Gaussian elimination */
    int pivot_row[NUM_UNK];
    memset(pivot_row, -1, sizeof(pivot_row));
    int cur_row = 0;

    for (int col = 0; col < NUM_UNK; col++) {
        int piv = -1;
        for (int row = cur_row; row < N; row++) {
            if (mat[row] & (1u << col)) { piv = row; break; }
        }
        if (piv == -1) continue;

        /* Swap */
        uint32_t tmp_m = mat[piv]; mat[piv] = mat[cur_row]; mat[cur_row] = tmp_m;
        int tmp_r = rhs_bits[piv]; rhs_bits[piv] = rhs_bits[cur_row]; rhs_bits[cur_row] = tmp_r;

        pivot_row[col] = cur_row;
        for (int row = 0; row < N; row++) {
            if (row != cur_row && (mat[row] & (1u << col))) {
                mat[row] ^= mat[cur_row];
                rhs_bits[row] ^= rhs_bits[cur_row];
            }
        }
        cur_row++;
    }

    /* Check consistency */
    for (int row = 0; row < N; row++) {
        if (mat[row] == 0 && rhs_bits[row] == 1) return -1;
    }

    /* Particular solution */
    memset(particular, 0, NUM_UNK * sizeof(int));
    for (int col = 0; col < NUM_UNK; col++) {
        if (pivot_row[col] >= 0)
            particular[col] = rhs_bits[pivot_row[col]];
    }

    /* Null space */
    int free_cols[13], num_free = 0;
    for (int col = 0; col < NUM_UNK; col++) {
        if (pivot_row[col] < 0)
            free_cols[num_free++] = col;
    }

    for (int fi = 0; fi < num_free; fi++) {
        memset(null_vecs[fi], 0, NUM_UNK * sizeof(int));
        null_vecs[fi][free_cols[fi]] = 1;
        for (int col = 0; col < NUM_UNK; col++) {
            if (pivot_row[col] >= 0 && (mat[pivot_row[col]] & (1u << free_cols[fi])))
                null_vecs[fi][col] = 1;
        }
    }

    return num_free;
}

/* Precomputed consistency check matrix T (rows for non-pivot equations) */
static uint32_t consistency_T[20];
static int num_consistency;

void compute_consistency_T(void) {
    uint32_t mat[N];
    uint32_t T[N];

    for (int row = 0; row < N; row++) {
        uint32_t r = 0;
        for (int idx = 0; idx < NUM_UNK; idx++) {
            if (A_mat[row] & (1u << unk_pos[idx]))
                r |= (1u << idx);
        }
        mat[row] = r;
        T[row] = (1u << row);
    }

    int cur_row = 0;
    for (int col = 0; col < NUM_UNK; col++) {
        int piv = -1;
        for (int row = cur_row; row < N; row++) {
            if (mat[row] & (1u << col)) { piv = row; break; }
        }
        if (piv == -1) continue;

        uint32_t tmp;
        tmp = mat[piv]; mat[piv] = mat[cur_row]; mat[cur_row] = tmp;
        tmp = T[piv]; T[piv] = T[cur_row]; T[cur_row] = tmp;

        for (int row = 0; row < N; row++) {
            if (row != cur_row && (mat[row] & (1u << col))) {
                mat[row] ^= mat[cur_row];
                T[row] ^= T[cur_row];
            }
        }
        cur_row++;
    }

    num_consistency = N - cur_row;
    for (int i = 0; i < num_consistency; i++)
        consistency_T[i] = T[cur_row + i];
}

/* Known column vectors for adjustment */
static uint32_t known_cols[NUM_KNOWN];

void precompute_known_cols(void) {
    for (int ki = 0; ki < NUM_KNOWN; ki++) {
        uint32_t col = 0;
        for (int row = 0; row < N; row++) {
            if (A_mat[row] & (1u << known_pos[ki]))
                col |= (1u << row);
        }
        known_cols[ki] = col;
    }
}

uint32_t get_adjusted_rhs(int k, uint32_t b_val) {
    uint32_t target_bits = 0;
    for (int i = 0; i < N; i++)
        target_bits |= (((target[i] >> k) & 1) << i);
    uint32_t rhs = target_bits ^ b_val;
    for (int ki = 0; ki < NUM_KNOWN; ki++) {
        if ((known_val[ki] >> k) & 1)
            rhs ^= known_cols[ki];
    }
    return rhs;
}

/* DFS solver */
static int found = 0;
static uint8_t solution[N];

void dfs(int k, uint8_t *flag) {
    if (found) return;

    if (k == 8) {
        /* Check printability */
        for (int i = 6; i < 31; i++) {
            if (flag[i] < 0x20 || flag[i] > 0x7e) return;
        }
        /* Verify */
        uint8_t out[N];
        forward(flag, out);
        if (memcmp(out, target, N) == 0) {
            memcpy(solution, flag, N);
            found = 1;
        }
        return;
    }

    /* Compute b_k */
    uint32_t b = compute_b(k, flag);
    uint32_t rhs = get_adjusted_rhs(k, b);

    /* Solve GF(2) system */
    int particular[NUM_UNK];
    int null_vecs[13][NUM_UNK];
    int num_free = solve_gf2(rhs, particular, null_vecs);
    if (num_free < 0) return; /* Inconsistent */

    if (k < 7) {
        /* Use carry-consistency to constrain null combo */

        /* Apply particular solution first */
        uint8_t base_flag[N];
        memcpy(base_flag, flag, N);
        for (int idx = 0; idx < NUM_UNK; idx++)
            base_flag[unk_pos[idx]] |= (particular[idx] << k);

        /* Compute b_{k+1} for base */
        uint32_t b_next_base = compute_b(k+1, base_flag);
        uint32_t adj_rhs_base = get_adjusted_rhs(k+1, b_next_base);

        /* Compute consistency bits for base */
        int cons_base[20];
        for (int r = 0; r < num_consistency; r++)
            cons_base[r] = __builtin_popcount(consistency_T[r] & adj_rhs_base) & 1;

        /* Compute deltas for each null vector */
        uint32_t cons_mat[20]; /* bitmask: bit j = consistency row r dot delta_j */
        memset(cons_mat, 0, sizeof(cons_mat));

        for (int j = 0; j < num_free; j++) {
            uint8_t flipped[N];
            memcpy(flipped, base_flag, N);
            for (int idx = 0; idx < NUM_UNK; idx++) {
                if (null_vecs[j][idx])
                    flipped[unk_pos[idx]] ^= (1 << k);
            }
            uint32_t b_next_flip = compute_b(k+1, flipped);
            uint32_t delta = b_next_base ^ b_next_flip;

            for (int r = 0; r < num_consistency; r++) {
                if (__builtin_popcount(consistency_T[r] & delta) & 1)
                    cons_mat[r] |= (1u << j);
            }
        }

        /* Solve consistency system: cons_mat * c = cons_base */
        /* Small system: 20 equations in num_free unknowns */
        uint32_t cm[20];
        int cr[20];
        memcpy(cm, cons_mat, sizeof(cm));
        memcpy(cr, cons_base, sizeof(cr));

        int pivot[13];
        memset(pivot, -1, sizeof(pivot));
        int crow = 0;
        for (int col = 0; col < num_free; col++) {
            int piv = -1;
            for (int row = crow; row < num_consistency; row++) {
                if (cm[row] & (1u << col)) { piv = row; break; }
            }
            if (piv == -1) continue;
            uint32_t t; int ti;
            t = cm[piv]; cm[piv] = cm[crow]; cm[crow] = t;
            ti = cr[piv]; cr[piv] = cr[crow]; cr[crow] = ti;
            pivot[col] = crow;
            for (int row = 0; row < num_consistency; row++) {
                if (row != crow && (cm[row] & (1u << col))) {
                    cm[row] ^= cm[crow];
                    cr[row] ^= cr[crow];
                }
            }
            crow++;
        }

        /* Check consistency of the consistency system */
        for (int row = 0; row < num_consistency; row++) {
            if (cm[row] == 0 && cr[row] == 1) return; /* No valid combo */
        }

        /* Find free vars in consistency system */
        int cfree[13], ncfree = 0;
        for (int col = 0; col < num_free; col++) {
            if (pivot[col] < 0)
                cfree[ncfree++] = col;
        }

        /* Enumerate valid combos */
        uint64_t total_combos = 1ULL << ncfree;
        for (uint64_t cbits = 0; cbits < total_combos; cbits++) {
            if (found) return;

            int combo[13] = {0};
            /* Set free vars */
            for (int fi = 0; fi < ncfree; fi++)
                combo[cfree[fi]] = (cbits >> fi) & 1;
            /* Solve for pivot vars */
            for (int col = 0; col < num_free; col++) {
                if (pivot[col] >= 0) {
                    int val = cr[pivot[col]];
                    for (int fi = 0; fi < ncfree; fi++) {
                        if (cm[pivot[col]] & (1u << cfree[fi]))
                            val ^= ((cbits >> fi) & 1);
                    }
                    combo[col] = val;
                }
            }

            /* Apply combo to flag */
            uint8_t new_flag[N];
            memcpy(new_flag, flag, N);
            for (int idx = 0; idx < NUM_UNK; idx++) {
                int bit = particular[idx];
                for (int j = 0; j < num_free; j++) {
                    if (combo[j] && null_vecs[j][idx])
                        bit ^= 1;
                }
                new_flag[unk_pos[idx]] |= (bit << k);
            }
            /* Restore known values */
            for (int ki = 0; ki < NUM_KNOWN; ki++)
                new_flag[known_pos[ki]] = known_val[ki];

            dfs(k+1, new_flag);
        }
    } else {
        /* Bit 7: enumerate all null combos, check printability */
        uint64_t total = 1ULL << num_free;
        for (uint64_t bits = 0; bits < total; bits++) {
            if (found) return;

            uint8_t new_flag[N];
            memcpy(new_flag, flag, N);
            for (int idx = 0; idx < NUM_UNK; idx++) {
                int bit = particular[idx];
                for (int j = 0; j < num_free; j++) {
                    if ((bits >> j) & 1) {
                        if (null_vecs[j][idx])
                            bit ^= 1;
                    }
                }
                new_flag[unk_pos[idx]] |= (bit << k);
            }
            for (int ki = 0; ki < NUM_KNOWN; ki++)
                new_flag[known_pos[ki]] = known_val[ki];

            /* Quick printability check */
            int ok = 1;
            for (int i = 6; i < 31; i++) {
                if (new_flag[i] < 0x20 || new_flag[i] > 0x7e) { ok = 0; break; }
            }
            if (!ok) continue;

            /* Verify */
            uint8_t out[N];
            forward(new_flag, out);
            if (memcmp(out, target, N) == 0) {
                memcpy(solution, new_flag, N);
                found = 1;
                return;
            }
        }
    }
}

int main(void) {
    /* Set up unknown positions */
    int is_known[N] = {0};
    for (int i = 0; i < NUM_KNOWN; i++) is_known[known_pos[i]] = 1;
    int ui = 0;
    for (int i = 0; i < N; i++) {
        if (!is_known[i]) unk_pos[ui++] = i;
    }

    printf("Building A matrix...\n");
    build_A();

    printf("Computing consistency check matrix...\n");
    compute_consistency_T();
    precompute_known_cols();
    printf("  Consistency equations: %d\n", num_consistency);

    printf("Starting DFS...\n");
    uint8_t flag[N] = {0};
    for (int i = 0; i < NUM_KNOWN; i++)
        flag[known_pos[i]] = known_val[i];

    dfs(0, flag);

    if (found) {
        printf("\nFLAG: ");
        for (int i = 0; i < N; i++) printf("%c", solution[i]);
        printf("\n");

        /* Verify */
        uint8_t out[N];
        forward(solution, out);
        printf("Verify: %s\n", memcmp(out, target, N) == 0 ? "PASS" : "FAIL");
    } else {
        printf("\nNo solution found.\n");
    }

    return 0;
}
