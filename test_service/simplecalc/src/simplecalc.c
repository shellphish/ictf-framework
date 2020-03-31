#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

char user[100] = {0};
char password[100] = {0};
char title[100] = {0};

void check_user_pass() {
    int userlen = strlen(user);
    int passlen = strlen(password);
    int i;
    for (i = 0; i < userlen; i++) {
        if (!isalnum(user[i])) {
            puts("username and pass should be alphanumeric!");
            exit(0);
        }
    }
    for (i = 0; i < passlen; i++) {
        if (!isalnum(password[i])) {
            puts("username and pass should be alphanumeric!");
            exit(0);
        }
    }
}


int process_rhs(char *curr, int *variables) {
    int index1;
    int const_val;
    char op;
    if (sscanf(curr, "V%d%c%d", &index1, &op, &const_val) != 3) {
        puts("Right side of equation must be a variable, an operator, and a constant!");
        exit(0);
    }
    if (index1 > 20) {
        puts("index out of bounds!");
        exit(0);
    }

    int val1 = variables[index1];
    if (op == '+') {
        return val1+const_val;
    }
    else if (op == '-') {
        return val1-const_val;
    }
    else if (op == '*') {
        return val1*const_val;
    }
    else if (op == '/') {
        return val1/const_val;
    }
    else {
        puts("unknown operator");
        exit(0);
    }
}

void process_eqn(char *eqn, int *variables) {
    int lhs_var;
    if (sscanf(eqn, "V%d", &lhs_var) != 1) {
        puts("Left side should be a variable!");
        exit(0);
    }
    char* curr = strchr(eqn, '=');
    if (curr == NULL) {
        puts("missing = sign");
        exit(0);
    }
    curr += 1;
    int val = process_rhs(curr, variables);
    variables[lhs_var] = val;
}

void save_results(int *variables) {
    char file_path[200];
    snprintf(file_path, 200, "/home/chall/service/rw/%s_%s", user, password);
    FILE* f = fopen(file_path, "w");
    fprintf(f, "%s\n", title);
    int i;
    for (i = 0; i < 20; i++) {
        fprintf(f, "V%d: %d\n", i, variables[i]);
    }
    fclose(f);
}

void solve() {
    char curr_eqn[32];
    int variables[20];
    memset(variables, 0, sizeof(variables));
    puts("Enter equations, use a blank line to end");
    while(1) {
        fgets(curr_eqn, 32, stdin);
        if (curr_eqn[0] == '\n') {
            break;
        } else {
            process_eqn(curr_eqn, variables);
        }
    }
    save_results(variables);
}

void retrieve() {
    char command[200];
    snprintf(command, 200, "cat /home/chall/service/rw/%s_%s", user, password);
    system(command);
}

void main_loop() {
    char input[16];
    while(1) {
        puts("<S>olve eqns or <R>etrieve result");
        fgets(input, 16, stdin);
        if (input[0] == 'S') {
            solve();
        }
        else if (input[0] == 'R') {
            retrieve();
        }
        else {
            return;
        }
    }
}

void strip(char *s) {
    int pos = strlen(s) - 1;
    if (s[pos] == '\n')
        s[pos] = '\0';
}

int main() {

    setbuf(stdout, NULL);
    setbuf(stdin, NULL);

    puts("Welcome to the basic calculator service!");
    puts("I will solve a small set of equations");
    puts("Use variables V0 to V19, which are all initialized to 0");
    puts("Example:");
    puts("V2=V3+12\nV1=V2*1337\n");
    puts("And save your results in your protected file");

    puts("Enter username:");
    fgets(user, 100, stdin);
    strip(user);

    puts("Enter password:");
    fgets(password, 100, stdin);
    strip(password);

    puts("Enter title of work:");
    fgets(title, 100, stdin);
    strip(title);

    check_user_pass();
    main_loop();
    return 0;
}
