package targetpackage;

public class TargetClass {
    public T proceed() throws Throwable {
		try {
			return constructor().newInstance(args);
		} catch (InvocationTargetException e) {
			throw e.getTargetException();
		}
	}
}
