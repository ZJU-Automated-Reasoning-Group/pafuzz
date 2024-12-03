#include <clang-c/Index.h>
#include <stdio.h>
#include <stdlib.h>

void print_function_info(CXCursor cursor) {

    // Retrieve function name
    CXString function_name = clang_getCursorSpelling(cursor);

    // Retrieve function location
    CXSourceLocation location = clang_getCursorLocation(cursor);
    CXFile file;
    unsigned line, column, offset;
    clang_getFileLocation(location, &file, &line, &column, &offset);

    // Retrieve function type
    CXType function_type = clang_getCursorResultType(cursor);
    CXString type_spelling = clang_getTypeSpelling(function_type);

    // Print function information
    CXCursor definitionCursor = clang_getCursorDefinition(cursor);
    const char *functionType = clang_equalCursors(cursor, definitionCursor) ? "Definition" : "Declaration";
    printf("%s: %s; Type: %s; Filename: %s; Line: %u; Column: %u; Parameter list: (", functionType, clang_getCString(function_name), clang_getCString(type_spelling), clang_getCString(clang_getFileName(file)), line, column);

    int numArgs = clang_Cursor_getNumArguments(cursor);
    for (int i = 0; i < numArgs; i++) {
        CXCursor argCursor = clang_Cursor_getArgument(cursor, i);
        CXType argType = clang_getCursorType(argCursor);
        if (i == 0) {
            printf("%s", clang_getCString(clang_getTypeSpelling(argType)));
        }
        else {
            printf(", %s", clang_getCString(clang_getTypeSpelling(argType)));
        }
    }
    printf(")\n");

    // Dispose of CXStrings
    clang_disposeString(function_name);
    clang_disposeString(type_spelling);
}

void print_varaible_info(CXCursor cursor, CXCursor parent) {
    CXString name = clang_getCursorSpelling(cursor);
    CXSourceRange range = clang_getCursorExtent(cursor);
    CXSourceLocation startLocation = clang_getRangeStart(range);
    CXSourceLocation endLocation = clang_getRangeEnd(range);

    unsigned line, column, offset;
    unsigned endline, endcolumn, endoffset;
    CXFile file, endfile;


    clang_getFileLocation(startLocation, &file, &line, &column, &offset);
    clang_getFileLocation(endLocation, &endfile, &endline, &endcolumn, &endoffset);
    CXString filename = clang_getFileName(file);


    CXType var_type = clang_getCursorType(cursor);
    CXString type_spelling = clang_getTypeSpelling(var_type);


    enum CXCursorKind parent_kind = clang_getCursorKind(parent);
    const char *scope = "";
    CXString scope_name = {"", 0};


    if (parent_kind == CXCursor_TranslationUnit) {
        scope = "Global";


        printf("Variable: %s; Type: %s; Scope: %s; Filename: %s; Line: %u; Column: %u; endColumn: %u\n",
            clang_getCString(name), clang_getCString(type_spelling), scope, clang_getCString(filename), line, column, endcolumn);

    } else {
        scope = "Local";

        CXCursor semantic_parent = clang_getCursorSemanticParent(cursor);
        if (clang_getCursorKind(semantic_parent) == CXCursor_FunctionDecl) {
            scope_name = clang_getCursorSpelling(semantic_parent);
        }
        printf("Variable: %s; Type: %s; Scope: %s (in %s); Filename: %s; Line: %u; Column: %u; endColumn: %u\n",
            clang_getCString(name), clang_getCString(type_spelling), scope,
            clang_getCString(scope_name), clang_getCString(filename), line, column, endcolumn);
    }


    clang_disposeString(name);
    clang_disposeString(filename);
    clang_disposeString(type_spelling);
    if (scope_name.data) {
        clang_disposeString(scope_name);
    }
}

enum CXChildVisitResult fieldVisitor(CXCursor fieldCursor, CXCursor parent, CXClientData client_data) {
    CXString parent_name = clang_getCursorSpelling(parent);
    if (clang_getCursorKind(fieldCursor) == CXCursor_FieldDecl) {
        CXString fieldName = clang_getCursorSpelling(fieldCursor);
        CXType fieldType = clang_getCursorType(fieldCursor);
        // printf("Field Name: %s\n", clang_getCString(fieldName));
        // printf("Field Type: %s\n", clang_getCString(clang_getTypeSpelling(fieldType)));

        CXSourceRange range = clang_getCursorExtent(fieldCursor);
        CXSourceLocation startLocation = clang_getRangeStart(range);
        CXSourceLocation endLocation = clang_getRangeEnd(range);

        CXFile startFile, endFile;
        unsigned int startLine, startColumn, startOffset;
        unsigned int endLine, endColumn, endOffset;

        clang_getFileLocation(startLocation, &startFile, &startLine, &startColumn, &startOffset);
        clang_getFileLocation(endLocation, &endFile, &endLine, &endColumn, &endOffset);
        // printf("Start Location - Line: %u, Column: %u\n", startLine, startColumn);
        // printf("End Location - Line: %u, Column: %u\n", endLine, endColumn);

        printf("Struct: %s; Type: %s; Name: %s; Filename: %s; Line: %u; Column: %u; endColumn: %u\n",
            clang_getCString(parent_name), clang_getCString(clang_getTypeSpelling(fieldType)), clang_getCString(fieldName), clang_getCString(clang_getFileName(startFile)), startLine, startColumn, endColumn);
        // printf("Variable: %s; Type: %s; Scope: Local (in Struct %s); Line: %u; Column: %u; endColumn: %u\n",
        //     clang_getCString(fieldName), clang_getCString(clang_getTypeSpelling(fieldType)), clang_getCString(parent_name), startLine, startColumn, endColumn);
        clang_disposeString(fieldName);
    }
    clang_disposeString(parent_name);
    return CXChildVisit_Continue;
}

void print_struct_info(CXCursor cursor) {
    CXString structName = clang_getCursorSpelling(cursor);

    CXSourceRange range = clang_getCursorExtent(cursor);
    CXSourceLocation startLocation = clang_getRangeStart(range);
    CXSourceLocation endLocation = clang_getRangeEnd(range);

    unsigned line, column, offset;
    unsigned endline, endcolumn, endoffset;
    CXFile file, endfile;


    clang_getFileLocation(startLocation, &file, &line, &column, &offset);
    clang_getFileLocation(endLocation, &endfile, &endline, &endcolumn, &endoffset);
    CXString filename = clang_getFileName(file);


    CXType var_type = clang_getCursorType(cursor);
    CXString type_spelling = clang_getTypeSpelling(var_type);

    printf("Struct: %s; Type: %s; Filename: %s; Line: %u; Column: %u; endLine: %u; endColumn: %u\n",
        clang_getCString(structName), clang_getCString(type_spelling), clang_getCString(filename), line, column, endline, endcolumn);

    clang_visitChildren(cursor, fieldVisitor, NULL);

    clang_disposeString(structName);
}

enum CXChildVisitResult findLoops(CXCursor fieldCursor, CXCursor parent, CXClientData client_data) {
    if (clang_getCursorKind(fieldCursor) == CXCursor_ForStmt) {
        CXSourceLocation location = clang_getCursorLocation(fieldCursor);
        CXString fileName;
        unsigned line, column;
        clang_getPresumedLocation(location, &fileName, &line, &column);

        printf("Loop; Filename: %s; Line: %u; Column: %u\n", clang_getCString(fileName), line, column);

        clang_disposeString(fileName);
        // clang_visitChildren(fieldCursor, findLoops, NULL);
    }
    return CXChildVisit_Continue;
}

void print_loop_info(CXCursor cursor) {
    CXSourceLocation location = clang_getCursorLocation(cursor);
    CXString fileName;
    unsigned line, column;
    clang_getPresumedLocation(location, &fileName, &line, &column);

    printf("Loop; Filename: %s; Line: %u; Column: %u\n", clang_getCString(fileName), line, column);

    // clang_visitChildren(cursor, findLoops, NULL);

    clang_disposeString(fileName);
}

enum CXChildVisitResult visit_node(CXCursor cursor, CXCursor parent, CXClientData client_data) {
    // Check if the cursor represents a function or method declaration
    enum CXCursorKind kind = clang_getCursorKind(cursor);
    if (kind == CXCursor_FunctionDecl || kind == CXCursor_CXXMethod) {
        print_function_info(cursor);
    }
    if (kind == CXCursor_VarDecl || kind == CXCursor_ParmDecl) {
        print_varaible_info(cursor, parent);
    }
    if (kind == CXCursor_StructDecl) {
        print_struct_info(cursor);
    }
    if (kind == CXCursor_ForStmt) {
        print_loop_info(cursor);
    }
    return CXChildVisit_Recurse;
}

void parse_file(const char* filename) {
    // Create translation unit from file
    CXIndex index = clang_createIndex(0, 0);
    CXTranslationUnit translation_unit = clang_parseTranslationUnit(index, filename, NULL, 0, NULL, 0, CXTranslationUnit_None);

    // Check for parsing errors
    if (translation_unit == NULL) {
        fprintf(stderr, "Unable to parse translation unit. Quitting.\n");
        exit(-1);
    }

    // Get translation unit cursor
    CXCursor cursor = clang_getTranslationUnitCursor(translation_unit);

    // Visit all children (functions) in the translation unit
    clang_visitChildren(cursor, visit_node, NULL);

    // Dispose of translation unit and index
    clang_disposeTranslationUnit(translation_unit);
    clang_disposeIndex(index);
}

// clang-16 main.c -L/usr/lib/llvm-16/lib -lclang -I/usr/lib/llvm-16/include -o toolc
int main(int argc, char** argv) {
    // Check for correct usage
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return -1;
    }

    // Parse and analyze the given C file
    // printf("{");
    parse_file(argv[1]);
    // printf("}");

    return 0;
}