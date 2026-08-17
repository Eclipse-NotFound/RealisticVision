// 编译期存根：运行时经子 ApplicationDomain 解析到游戏真实类（勿随模组 SWF 发布）
package fe.weapon
{
   import fe.Pt;
   import fe.unit.Unit;

   public class Weapon extends Pt
   {
      public var owner:Unit;
   }
}
