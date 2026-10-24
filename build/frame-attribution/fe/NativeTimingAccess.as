package fe {
   /** Test-only same-package reader; no writes to native state. */
   public final class NativeTimingAccess {
      public static function tick(world:*):int {
         return world.t_save;
      }
   }
}
