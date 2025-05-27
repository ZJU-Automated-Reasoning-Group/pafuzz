#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Instruction.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/DebugInfo.h"
#include "llvm/IR/DebugLoc.h"
#include "llvm/IR/DIBuilder.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/Intrinsics.h"
#include <vector>
#include <map>
#include <string>

using namespace llvm;

namespace {
    struct IndirectCallInfo {
        std::string CallerFunction;
        std::string FileName;
        unsigned LineNumber;
        unsigned ColumnNumber;
        uint32_t CallSiteId;
    };

    class AFLIndirectCallTracker : public ModulePass {
    public:
        static char ID;
        AFLIndirectCallTracker() : ModulePass(ID) {}

        bool runOnModule(Module &M) override {
            LLVMContext &C = M.getContext();
            
            // Create global variables and structures for tracking
            GlobalVariable *CallSiteCounter = createGlobalCounter(M, "__afl_indirect_call_site_counter");
            GlobalVariable *CallInfoArray = createCallInfoArray(M);
            
            // Get or create the logging function
            Function *LogFunc = getOrCreateLogFunction(M);
            Function *ResolveNameFunc = getOrCreateResolveNameFunction(M);
            
            bool ModifiedIR = false;
            std::vector<std::pair<CallInst*, IndirectCallInfo>> IndirectCalls;
            uint32_t CallSiteId = 0;
            
            // Collect all indirect call sites with metadata
            for (Function &F : M) {
                if (F.isDeclaration()) continue;
                
                for (BasicBlock &BB : F) {
                    for (Instruction &I : BB) {
                        if (CallInst *CI = dyn_cast<CallInst>(&I)) {
                            // Check if this is an indirect call
                            if (!CI->getCalledFunction()) {
                                IndirectCallInfo Info = extractCallInfo(CI, F, CallSiteId++);
                                IndirectCalls.push_back({CI, Info});
                            }
                        }
                    }
                }
            }
            
            // Create static call site information
            createStaticCallSiteInfo(M, IndirectCalls);
            
            // Instrument each indirect call site
            for (auto &Pair : IndirectCalls) {
                instrumentIndirectCall(Pair.first, Pair.second, LogFunc, ResolveNameFunc, M);
                ModifiedIR = true;
            }
            
            return ModifiedIR;
        }

    private:
        IndirectCallInfo extractCallInfo(CallInst *CI, Function &F, uint32_t CallSiteId) {
            IndirectCallInfo Info;
            Info.CallerFunction = F.getName().str();
            Info.CallSiteId = CallSiteId;
            Info.FileName = "unknown";
            Info.LineNumber = 0;
            Info.ColumnNumber = 0;
            
            // Extract debug information if available
            if (const DebugLoc &DL = CI->getDebugLoc()) {
                Info.LineNumber = DL.getLine();
                Info.ColumnNumber = DL.getCol();
                
                if (DIScope *Scope = DL.getScope()) {
                    if (DIFile *File = Scope->getFile()) {
                        Info.FileName = File->getFilename().str();
                    }
                }
            }
            
            return Info;
        }

        GlobalVariable* createGlobalCounter(Module &M, const std::string &Name) {
            LLVMContext &C = M.getContext();
            Type *Int32Ty = Type::getInt32Ty(C);
            
            GlobalVariable *Counter = new GlobalVariable(
                M, Int32Ty, false, GlobalValue::ExternalLinkage,
                ConstantInt::get(Int32Ty, 0), Name);
            
            return Counter;
        }
        
        GlobalVariable* createCallInfoArray(Module &M) {
            LLVMContext &C = M.getContext();
            Type *Int8PtrTy = Type::getInt8PtrTy(C);
            
            // Create array for storing call site info strings
            ArrayType *ArrayTy = ArrayType::get(Int8PtrTy, 65536);
            
            GlobalVariable *InfoArray = new GlobalVariable(
                M, ArrayTy, false, GlobalValue::ExternalLinkage,
                ConstantAggregateZero::get(ArrayTy), "__afl_call_site_info");
            
            return InfoArray;
        }
        
        void createStaticCallSiteInfo(Module &M, 
                                    const std::vector<std::pair<CallInst*, IndirectCallInfo>> &IndirectCalls) {
            LLVMContext &C = M.getContext();
            
            // Create global strings for each call site
            for (const auto &Pair : IndirectCalls) {
                const IndirectCallInfo &Info = Pair.second;
                
                std::string InfoStr = Info.CallerFunction + ":" + Info.FileName + ":" + 
                                    std::to_string(Info.LineNumber) + ":" + 
                                    std::to_string(Info.ColumnNumber);
                
                // Create global string constant
                Constant *InfoStrConstant = ConstantDataArray::getString(C, InfoStr, true);
                GlobalVariable *InfoStrGlobal = new GlobalVariable(
                    M, InfoStrConstant->getType(), true, GlobalValue::PrivateLinkage,
                    InfoStrConstant, "__afl_call_site_" + std::to_string(Info.CallSiteId));
            }
        }
        
        Function* getOrCreateLogFunction(Module &M) {
            LLVMContext &C = M.getContext();
            
            Function *LogFunc = M.getFunction("__afl_log_indirect_call");
            if (LogFunc) {
                return LogFunc;
            }
            
            // void __afl_log_indirect_call(int call_site_id, void* target_func, 
            //                              char* caller_info, char* target_name)
            Type *VoidTy = Type::getVoidTy(C);
            Type *Int32Ty = Type::getInt32Ty(C);
            Type *Int8PtrTy = Type::getInt8PtrTy(C);
            
            FunctionType *LogFuncTy = FunctionType::get(
                VoidTy, {Int32Ty, Int8PtrTy, Int8PtrTy, Int8PtrTy}, false);
            
            LogFunc = Function::Create(
                LogFuncTy, Function::ExternalLinkage,
                "__afl_log_indirect_call", &M);
            
            return LogFunc;
        }
        
        Function* getOrCreateResolveNameFunction(Module &M) {
            LLVMContext &C = M.getContext();
            
            Function *ResolveFunc = M.getFunction("__afl_resolve_function_name");
            if (ResolveFunc) {
                return ResolveFunc;
            }
            
            // char* __afl_resolve_function_name(void* func_ptr)
            Type *Int8PtrTy = Type::getInt8PtrTy(C);
            
            FunctionType *ResolveFuncTy = FunctionType::get(
                Int8PtrTy, {Int8PtrTy}, false);
            
            ResolveFunc = Function::Create(
                ResolveFuncTy, Function::ExternalLinkage,
                "__afl_resolve_function_name", &M);
            
            return ResolveFunc;
        }
        
        void instrumentIndirectCall(CallInst *CI, const IndirectCallInfo &Info,
                                  Function *LogFunc, Function *ResolveNameFunc, Module &M) {
            LLVMContext &C = M.getContext();
            IRBuilder<> Builder(CI);
            
            // Get the called value (function pointer)
            Value *CalledValue = CI->getCalledValue();
            
            // Cast function pointer to i8*
            Value *FuncPtr = Builder.CreateBitCast(
                CalledValue, Type::getInt8PtrTy(C), "func_ptr");
            
            // Create call site info string
            std::string CallerInfo = Info.CallerFunction + ":" + Info.FileName + ":" + 
                                   std::to_string(Info.LineNumber) + ":" + 
                                   std::to_string(Info.ColumnNumber);
            
            // Create global string for caller info
            Constant *CallerInfoStr = ConstantDataArray::getString(C, CallerInfo, true);
            GlobalVariable *CallerInfoGlobal = new GlobalVariable(
                M, CallerInfoStr->getType(), true, GlobalValue::PrivateLinkage,
                CallerInfoStr, "__afl_caller_info_" + std::to_string(Info.CallSiteId));
            
            // Get pointer to the string
            Value *CallerInfoPtr = Builder.CreateInBoundsGEP(
                CallerInfoStr->getType(), CallerInfoGlobal,
                {ConstantInt::get(Type::getInt32Ty(C), 0), 
                 ConstantInt::get(Type::getInt32Ty(C), 0)});
            
            // Resolve target function name at runtime
            Value *TargetName = Builder.CreateCall(ResolveNameFunc, {FuncPtr}, "target_name");
            
            // Call logging function
            Builder.CreateCall(LogFunc, {
                ConstantInt::get(Type::getInt32Ty(C), Info.CallSiteId),
                FuncPtr,
                CallerInfoPtr,
                TargetName
            });
        }
    };
}

char AFLIndirectCallTracker::ID = 0;

// Register the pass
static RegisterPass<AFLIndirectCallTracker> X(
    "afl-indirect-call-tracker", 
    "AFL Indirect Call Tracker Pass with Detailed Info",
    false, false);

// Register with pass manager
static void registerAFLIndirectCallTracker(const PassManagerBuilder &,
                                         legacy::PassManagerBase &PM) {
    PM.add(new AFLIndirectCallTracker());
}

static RegisterStandardPasses RegisterAFLIndirectCallTracker(
    PassManagerBuilder::EP_OptimizerLast,
    registerAFLIndirectCallTracker);

static RegisterStandardPasses RegisterAFLIndirectCallTracker0(
    PassManagerBuilder::EP_EnabledOnOptLevel0,
    registerAFLIndirectCallTracker);
    